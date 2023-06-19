import base64
import io
import json
import logging
import subprocess

import numpy as np
import requests
from PIL import Image
from pydantic import Field
from typing_extensions import Literal

from frigate.detectors.detection_api import DetectionApi
from frigate.detectors.detector_config import BaseDetectorConfig

logger = logging.getLogger(__name__)

DETECTOR_KEY = Literal("custom")


class UserSpecifiedDetectorConfig(BaseDetectorConfig):
    type: DETECTOR_KEY
    api_url: str = Field(default="", title="API URL")
    api_timeout: float = Field(default=0.1, title="API timeout (in seconds)")
    api_key: str = Field(default="", title="API key (if required)")
    response_fields: dict = Field(
        default={
            "predictions": "predictions",
            "confidence": "confidence",
            "label": "label",
            "y_min": "y_min",
            "x_min": "x_min",
            "y_max": "y_max",
            "x_max": "x_max",
        },
        title="Response field names",
    )
    image: dict = Field(
        default={"name": "image", "base64": False},
        title="Image field",
    )
    post_data: dict = Field(default={}, title="Post data")
    local: False if (
        api_url.startswith("https://") or api_url.startswith("http://")
    ) else True


class UserSpecifiedDetector(DetectionApi):
    type_key = DETECTOR_KEY

    def __init__(self, detector_config: UserSpecifiedDetectorConfig):
        self.api_url = detector_config.api_url
        self.api_timeout = detector_config.api_timeout
        self.api_key = detector_config.api_key
        self.labels = detector_config.model.merged_labelmap
        self.response_fields = detector_config.response_fields
        self.image = detector_config.image
        self.local = detector_config.local

    def get_label_index(self, label_value):
        if label_value.lower() == "truck":
            label_value = "car"
        for index, value in self.labels.items():
            if value == label_value.lower():
                return index
        return -1

    def detect_raw(self, tensor_input):
        image_data = np.squeeze(tensor_input).astype(np.uint8)
        image = Image.fromarray(image_data)
        self.w, self.h = image.size
        with io.BytesIO() as output:
            image.save(output, format="JPEG")
            image_bytes = output.getvalue()

        if self.local:
            # Execute local binary and capture output
            process = subprocess.Popen(
                [self.api_url],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = process.communicate(input=image_bytes)
            if process.returncode != 0:
                logger.error(f"Error executing local binary: {stderr.decode()}")
                return np.zeros((20, 6), np.float32)
            response_json = json.loads(stdout.decode())
            detections = np.zeros((20, 6), np.float32)
            if response_json.get(self.response_fields["predictions"]) is None:
                logger.debug(f"Error in parsing response json: {response_json}")
                return detections
        else:
            data = {"api_key": self.api_key}
            response = requests.post(
                self.api_url,
                data=self.post_data,
                files={
                    self.image["name"]: image_bytes
                    if self.image["base64"] is False
                    else base64.encode(image_bytes)
                },
                timeout=self.api_timeout,
            )
            response_json = response.json()

            detections = np.zeros((20, 6), np.float32)
            if response_json.get(self.response_fields["predictions"]) is None:
                logger.debug(f"Error in parsing response json: {response_json}")
                return detections

        for i, detection in enumerate(
            response_json.get(self.response_fields["predictions"])
        ):
            logger.debug(f"Response: {detection}")
            if detection[self.response_fields["confidence"]] < 0.4:
                logger.debug("Break due to confidence < 0.4")
                break
            label = self.get_label_index(detection[self.response_fields["label"]])
            if label < 0:
                logger.debug("Break due to unknown label")
                break
            detections[i] = [
                label,
                float(detection[self.response_fields["confidence"]]),
                detection[self.response_fields["y_min"]] / self.h,
                detection[self.response_fields["x_min"]] / self.w,
                detection[self.response_fields["y_max"]] / self.h,
                detection[self.response_fields["x_max"]] / self.w,
            ]

        return detections
