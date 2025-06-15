"""This module defines the output schema for the LLM output."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Image(BaseModel):
    """Represents an image used in a presentation slide."""

    path: str = Field(..., description="Exact image path from a predefined list.")
    caption: str = Field(..., description="Image caption text.")
    orientation: Literal["horizontal", "vertical", "square"] = Field(
        ..., description="Image orientation."
    )


class Slide(BaseModel):
    """Represents a slide in the presentation."""

    type: Literal["title", "introduction", "core_idea", "summary"] = Field(
        ..., description="Type of the slide."
    )
    title: Optional[str] = Field(
        None, description="Slide title, required only for 'core_idea' slides."
    )
    content_format: Optional[Literal["itemize", "text"]] = Field(
        None, description="Format of the slide content."
    )
    content: List[str] = Field(
        ..., description="List of bullet points or text paragraphs."
    )
    layout: Optional[Literal["text_only", "two_column", "single_image"]] = Field(
        None, description="Slide layout for 'core_idea' slides."
    )
    image: Optional[Image] = Field(
        None, description="Image object if layout is 'two_column' or 'single_image'."
    )


class Presentation(BaseModel):
    """Represents the entire presentation structure."""

    title: str = Field(..., description="Title of the presentation.")
    author: str = Field(..., description="Author of the presentation.")
    slides: List[Slide] = Field(..., description="List of slides in the presentation.")
