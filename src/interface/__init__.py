"""This module initializes the UI package."""

from .gradio_interface import demo
from .upload_files import upload_files

__all__ = ["upload_files", "demo"]
