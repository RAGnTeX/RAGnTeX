"""Telemetry utilities for Langfuse integration and OpenTelemetry tracing."""

import os
from functools import lru_cache

from langfuse import Langfuse
from langfuse.decorators import observe

from .logging_utils import Logger

LOGGER = Logger.get_logger()


@lru_cache()
def init_telemetry() -> Langfuse:
    """Setup langfuse for tracing."""
    # global TRACER
    return Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )


@observe(name="📝 submit_feedback")
def submit_feedback(rating: str, comment: str, trace_id: str, _session_id: str) -> str:
    """Submit user feedback with a star rating and optional comment.
    Args:
        rating (str): Star rating as a string of emojis (e.g., "⭐⭐⭐").
        comment (str): Optional user comment.
        trace_id (str): Langfuse trace ID for linking feedback.
        session_id (str): Unique identifier for the current session.
    Returns:
        str: Confirmation message indicating success or failure.
    """
    if not rating:
        return "⚠️ Please select a star rating before submitting."

    score = rating.count("⭐️")  # Converts emoji to numeric
    stars_display = "⭐️" * score + "☆" * (5 - score)
    tracer = init_telemetry()
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

    return (
        f"✅ Thanks for your {stars_display} rating!"
        f"{' Your comment: ' + comment if comment else ''}"
    )
