"""This module initializes the services package."""

from .google_client import client
from .output_schema import Presentation
from .prompt import build_prompt

__all__ = ["client", "build_prompt", "Presentation"]
