import time
import os
import logging
from frigate.version import VERSION
from opentelemetry import trace

tracer = trace.get_tracer(os.environ.get("OTEL_SERVICE_NAME", "frigate"), VERSION)
