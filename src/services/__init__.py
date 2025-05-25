"""This module initializes the services package."""

from .google_client import client
from .generator import generate_presentation

__all__ = ["client", "generate_presentation"]
