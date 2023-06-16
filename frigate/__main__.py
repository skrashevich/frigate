import faulthandler
import os
import threading
import uptrace
import grpc
from frigate.version import VERSION
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.sdk import metrics as sdkmetrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    AggregationTemporality,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.resources import Resource
from flask import cli

from frigate.app import FrigateApp

faulthandler.enable()

threading.current_thread().name = "frigate"

cli.show_server_banner = lambda *x: None

if __name__ == "__main__":
    uptrace.configure_opentelemetry(
        dsn=os.environ.get("UPTRACE_DSN"),
        service_name=os.environ.get("OTEL_SERVICE_NAME", "frigate"),
        service_version=VERSION,
        deployment_environment="production",
    )

    temporality_delta = {
        sdkmetrics.Counter: AggregationTemporality.DELTA,
        sdkmetrics.UpDownCounter: AggregationTemporality.DELTA,
        sdkmetrics.Histogram: AggregationTemporality.DELTA,
        sdkmetrics.ObservableCounter: AggregationTemporality.DELTA,
        sdkmetrics.ObservableUpDownCounter: AggregationTemporality.DELTA,
        sdkmetrics.ObservableGauge: AggregationTemporality.DELTA,
    }

    exporter = OTLPMetricExporter(
        endpoint="otlp.uptrace.dev:4317",
        headers=(("uptrace-dsn", os.environ.get("UPTRACE_DSN")),),
        timeout=5,
        compression=grpc.Compression.Gzip,
        preferred_temporality=temporality_delta,
    )
    reader = PeriodicExportingMetricReader(exporter)

    tracer = trace.get_tracer(os.environ.get("OTEL_SERVICE_NAME", "frigate"), VERSION)
    resource = Resource(
        attributes={
            "service.name": os.environ.get("OTEL_SERVICE_NAME", "frigate"),
            "service.version": VERSION,
        }
    )
    provider = MeterProvider(metric_readers=[reader], resource=resource)
    metrics.set_meter_provider(provider)

    meter = metrics.get_meter("github.com/uptrace/uptrace-python", "1.0.0")
    counter = meter.create_counter("some.prefix.counter", description="TODO")
    frigate_app = FrigateApp()

    frigate_app.start()
