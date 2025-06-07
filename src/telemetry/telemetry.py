"""Telemetry utilities for Langfuse integration and OpenTelemetry tracing."""

import os
import hashlib
from typing import Union
from contextlib import contextmanager

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


def hash_prompt(text: str) -> str:
    """Generate a SHA-256 hash of the prompt.
    Args:
        text (str): The input text to hash."""
    return hashlib.sha256(text.encode()).hexdigest()


@contextmanager
def traced_block(name: str, **attrs):
    """Context manager to create a traced block.
    Args:
        name (str): The name of the span.
        **attrs: Additional attributes to set on the span."""
    with tracer.start_as_current_span(name) as span:
        for key, value in attrs.items():
            span.set_attribute(key, value)
        try:
            # trace_id = format(span.get_span_context().trace_id, "032x")
            # yield span, trace_id
            yield span
        except Exception as e:
            # Record exception and mark span status as error
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            LOGGER.error("Error in span %s while generating content: %s", name, e)
            raise


def generate_with_trace(client, model_name: str, prompt: str) -> Union[object, None]:
    """Save traces from the generation.
    Args:
        client: google genai client instance.
        model_name (str): The name of the model to use.
        prompt (str): The input prompt for generation."""
    with tracer.start_as_current_span("🤖 genai_generate") as span:
        span.set_attribute("input.prompt_hash", hash_prompt(prompt))
        span.set_attribute("input.prompt_length", len(prompt))
        span.set_attribute("input.model_name", model_name)
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            span.set_attribute("output.response_length", len(str(response)))
            span.set_attribute("output.success", True)
            return response
        except Exception as e:
            span.set_attribute("output.success", False)
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            return LOGGER.error("Error in spans while generating content: %s", e)


def submit_feedback(rating: str, comment: str, trace_id: str) -> str:
    if not rating:
        return "⚠️ Please select a star rating before submitting."

    score = rating.count("⭐️")  # Converts emoji to numeric
    stars_display = "⭐️" * score + "☆" * (5 - score)

    # Submit to Langfuse if trace_id is present
    if trace_id:
        try:
            langfuse.feedback(
                trace_id=trace_id, name="user_feedback", comment=comment, score=score
            )
        except Exception as e:
            return f"✅ Feedback received ({stars_display}), but Langfuse logging failed: {e}"

    return f"✅ Thanks for your {stars_display} rating!{' Your comment: ' + comment if comment else ''}"
