import logging
import numpy as np
import requests

from frigate.detectors.detection_api import DetectionApi
from frigate.detectors.detector_config import BaseDetectorConfig
from typing import Literal
from pydantic import Extra, Field

logger = logging.getLogger(__name__)

DETECTOR_KEY = "deepstack"


class DeepstackDetectorConfig(BaseDetectorConfig):
    type: Literal[DETECTOR_KEY]
    api_url: str = Field(default="http://localhost:80/v1/vision/detection", title="DeepStack API URL")
    api_timeout: float = Field(default=10.0, title="DeepStack API timeout (in seconds)")
    api_key: str = Field(default="", title="DeepStack API key (if required)")

class DeepStack(DetectionApi):
    type_key = DETECTOR_KEY

    def __init__(self, detector_config: DeepstackDetectorConfig):
        self.api_url = detector_config.api_url
        self.api_timeout = detector_config.api_timeout
        self.api_key = detector_config.api_key

    def detect_raw(self, tensor_input):
        image_data = np.squeeze(tensor_input).astype(np.uint8)
        image_bytes = image_data.tobytes()
        data = {"api_key": self.api_key}
        response = requests.post(self.api_url, files={"image": image_bytes}, timeout=self.api_timeout)

        response_json = response.json()
        detections = np.zeros((20, 6), np.float32)

        for i, detection in enumerate(response_json["predictions"]):
            if detection["confidence"] < 0.4 or i == 20:
                break
            detections[i] = [
                detection["label"],
                detection["confidence"],
                detection["box"]["x_min"],
                detection["box"]["y_min"],
                detection["box"]["x_max"],
                detection["box"]["y_max"],
            ]

        return detections
