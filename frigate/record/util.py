"""Recordings Utilities."""

import os
import boto3
import tempfile
import logging
from frigate.config import FrigateConfig

logger = logging.getLogger(__name__)


def remove_empty_directories(directory: str) -> None:
    # List all directories recursively and sort them by path, longest first
    paths = sorted([x[0] for x in os.walk(directory)], key=len, reverse=True)
    # Use `os.scandir` for better performance
    for path in paths:
        if path == directory:
            continue
        if not any(os.scandir(path)):
            os.rmdir(path)
