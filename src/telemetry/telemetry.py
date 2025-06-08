"""Telemetry utilities for Langfuse integration and OpenTelemetry tracing."""

import os

from langfuse import Langfuse
from langfuse.decorators import observe

from .logging_utils import Logger

LOGGER = Logger.get_logger()

tracer = None


def init_telemetry() -> None:
    """Setup langfuse for tracing."""
    if os.getenv("USE_LANGFUSE", "false").lower() == "true":
        global tracer
        tracer = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            # otel_tracing_enabled=True,
        )
        assert tracer is not None, "Telemetry tracer not initialized"
    else:
        LOGGER.warning("Langfuse telemetry is disabled (USE_LANGFUSE != true)")


@observe(name="📝 submit_feedback")
def submit_feedback(rating: str, comment: str, trace_id: str) -> str:
    if not rating:
        return "⚠️ Please select a star rating before submitting."

    score = rating.count("⭐️")  # Converts emoji to numeric
    stars_display = "⭐️" * score + "☆" * (5 - score)

    # Submit to Langfuse if trace_id is present
    if trace_id:
        try:
            tracer.score(
                trace_id=trace_id,
                name="user_feedback",
                comment=comment or None,
                value=score,
            )
        except Exception as e:
            return f"✅ Feedback received ({stars_display}), but Langfuse logging failed: {e}"

    return f"✅ Thanks for your {stars_display} rating!{' Your comment: ' + comment if comment else ''}"
