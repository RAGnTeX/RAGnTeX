"""Initialize the package by exposing the main interface and telemetry setup."""

from .generator import generate_presentation
from .interface import demo
from .telemetry import init_telemetry

__all__ = [
    "demo",
    "init_telemetry",
    "generate_presentation",
]
