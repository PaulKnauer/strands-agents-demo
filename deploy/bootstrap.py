"""AgentCore bootstrap entrypoint.

Starts AWS Distro for OpenTelemetry auto-instrumentation before importing app.py,
while still satisfying AgentCore's requirement that the direct-code entry point be
a single Python file path.
"""

import os

# AgentCore observability docs require the AWS distro/configurator pair for Python.
os.environ.setdefault("OTEL_PYTHON_DISTRO", "aws_distro")
os.environ.setdefault("OTEL_PYTHON_CONFIGURATOR", "aws_configurator")
os.environ.setdefault("OTEL_PROPAGATORS", "xray,tracecontext,baggage")
os.environ.setdefault("AGENT_OBSERVABILITY_ENABLED", "true")
os.environ.setdefault("AWS_AGENTIC_OBSERVABILITY_OPT_IN", "true")
os.environ.setdefault("OTEL_SERVICE_NAME", os.environ.get("AGENT_NAME", "agentcore"))
os.environ.setdefault(
    "OTEL_RESOURCE_ATTRIBUTES",
    f"service.name={os.environ.get('AGENT_NAME', 'agentcore')}",
)
region = os.environ.get("AWS_REGION", "us-east-1")
os.environ.setdefault("OTEL_TRACES_EXPORTER", "otlp")
os.environ.setdefault("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")
os.environ.setdefault(
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    f"https://xray.{region}.amazonaws.com/v1/traces",
)

from opentelemetry.instrumentation.auto_instrumentation import (
    sitecustomize,
)  # noqa: F401

import app  # noqa: F401
