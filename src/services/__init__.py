"""This module initializes the services package."""

from .google_client import client, generate_with_retry, generate_slides_with_nanobanana
from .output_schema import Presentation
from .prompt import build_prompt

__all__ = [
    "client",
    "build_prompt",
    "Presentation",
    "generate_with_retry",
    "generate_slides_with_nanobanana",
]
