"""This module initializes the latex compilation package."""

from .json_to_tex import json_to_tex
from .latex_compilation import compile_presentation

__all__ = ["compile_presentation", "json_to_tex"]
