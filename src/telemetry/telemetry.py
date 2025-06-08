"""Telemetry utilities for Langfuse integration and OpenTelemetry tracing."""

import os

import base64
import langfuse
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from .logging_utils import Logger

LOGGER = Logger.get_logger()

tracer = None


def init_telemetry() -> None:
    """Setup langfuse, initialize OpenTelemetry for tracing."""
    if os.getenv("USE_LANGFUSE", "false").lower() == "true":
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = (
            os.environ["LANGFUSE_HOST"] + "/api/public/otel"
        )
        auth = f"{os.getenv('LANGFUSE_PUBLIC_KEY')}:{os.getenv('LANGFUSE_SECRET_KEY')}"
        auth_b64 = base64.b64encode(auth.encode()).decode()
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth_b64}"

        provider = TracerProvider()
        exporter = OTLPSpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        global tracer
        tracer = trace.get_tracer("langfuse.genai")

    else:
        LOGGER.warning("Langfuse telemetry is disabled (USE_LANGFUSE != true)")


def submit_feedback(rating: str, comment: str, trace_id: str) -> str:
    if not rating:
        return "⚠️ Please select a star rating before submitting."

    score = rating.count("⭐️")  # Converts emoji to numeric
    stars_display = "⭐️" * score + "☆" * (5 - score)

    # Submit to Langfuse if trace_id is present
    if trace_id:
        try:
            langfuse.feedback(
                trace_id=trace_id,
                name="user_feedback",
                comment=comment or None,
                score=score,
            )
        except Exception as e:
            return f"✅ Feedback received ({stars_display}), but Langfuse logging failed: {e}"

    return f"✅ Thanks for your {stars_display} rating!{' Your comment: ' + comment if comment else ''}"
