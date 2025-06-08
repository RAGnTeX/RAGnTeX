"""Initialize the package by exposing the main interface and telemetry setup."""

from .interface import demo
from .telemetry import init_telemetry
from .generator import generate_presentation

__all__ = [
    "demo",
    "init_telemetry",
    "generate_presentation",
]
