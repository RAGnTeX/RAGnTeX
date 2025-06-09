"""This module defines the output schema for the LLM output."""

from typing import Literal, Optional

from pydantic import BaseModel


class Image(BaseModel):
    """Represents an image used in a presentation slide."""

    path: str
    caption: str
    orientation: Literal["horizontal", "vertical", "square"]


class Slide(BaseModel):
    """Represents a slide in the presentation."""

    type: Literal["title", "introduction", "core_idea", "summary"]
    title: Optional[str] = None  # Used for core_idea slides
    content_format: Optional[Literal["itemize", "text"]]
    content: list[str]
    layout: Optional[Literal["text_only", "two_column", "single_image"]] = None
    image: Optional[Image] = None


class Presentation(BaseModel):
    """Represents the entire presentation structure."""

    title: str
    author: str
    slides: list[Slide]
