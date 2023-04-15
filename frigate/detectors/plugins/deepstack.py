import logging
import numpy as np
import requests
import io

from frigate.detectors.detection_api import DetectionApi
from frigate.detectors.detector_config import BaseDetectorConfig
from typing import Literal
from pydantic import Extra, Field
from PIL import Image


logger = logging.getLogger(__name__)

DETECTOR_KEY = "deepstack"


class DeepstackDetectorConfig(BaseDetectorConfig):
    type: Literal[DETECTOR_KEY]
    api_url: str = Field(default="http://localhost:80/v1/vision/detection", title="DeepStack API URL")
    api_timeout: float = Field(default=0.1, title="DeepStack API timeout (in seconds)")
    api_key: str = Field(default="", title="DeepStack API key (if required)")

class DeepStack(DetectionApi):
    type_key = DETECTOR_KEY

    def __init__(self, detector_config: DeepstackDetectorConfig):
        self.api_url = detector_config.api_url
        self.api_timeout = detector_config.api_timeout
        self.api_key = detector_config.api_key
        self.labels = self.load_labels("/labelmap.txt")

    def load_labels(self, path, encoding="utf-8"):
        """Loads labels from file (with or without index numbers).
        Args:
        path: path to label file.
        encoding: label file encoding.
        Returns:
        Dictionary mapping indices to labels.
        """
        with open(path, "r", encoding=encoding) as f:
            labels = {index: "unknown" for index in range(91)}
            lines = f.readlines()
            if not lines:
                return {}

            if lines[0].split(" ", maxsplit=1)[0].isdigit():
                pairs = [line.split(" ", maxsplit=1) for line in lines]
                labels.update({int(index): label.strip() for index, label in pairs})
            else:
                labels.update({index: line.strip() for index, line in enumerate(lines)})
            return labels
    
    def get_label_index(self, label_value):
        for index, value in self.labels.items():
            if value == label_value:
                return index
        return None
    
    def detect_raw(self, tensor_input):
        image_data = np.squeeze(tensor_input).astype(np.uint8)
        image = Image.fromarray(image_data)
        with io.BytesIO() as output:
            image.save(output, format="JPEG")
            image_bytes = output.getvalue()
        data = {"api_key": self.api_key}
        response = requests.post(self.api_url, files={"image": image_bytes}, timeout=self.api_timeout)
        response_json = response.json()
        detections = np.zeros((20, 6), np.float32)
       
        for i, detection in enumerate(response_json["predictions"]):
            if detection["confidence"] < 0.4:
                break
            detections[i] = [
                int(self.get_label_index(detection["label"])),
                float(detection["confidence"]),
                detection["y_min"],
                detection["x_min"],
                detection["y_max"],
                detection["x_max"],
            ]
            print(detections[i])

        return detections
