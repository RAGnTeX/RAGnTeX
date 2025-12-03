"""Initialize and export a GenAI client using the provided Google API key."""

from __future__ import annotations

import os
import time
from typing import Any
import base64

import httpx
from dotenv import load_dotenv
from google import genai
from google.api_core.exceptions import GoogleAPIError

from .output_schema import Presentation

# --------------------------------------------------------------------------- #
#  Globals
# --------------------------------------------------------------------------- #

load_dotenv()
GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY")

# A singleton Gemini client that the rest of the project can import.
client: genai.Client = genai.Client(api_key=GOOGLE_API_KEY)

# --------------------------------------------------------------------------- #
#  Public helpers
# --------------------------------------------------------------------------- #


def generate_with_retry(
    genai_client: genai.Client,
    model_name: str,
    prompt: str,
    *,
    max_retries: int = 3,
    retry_delay: int = 2,
) -> Any:
    """Generate content using the specified model with retry logic for transient errors.

    Args:
        client (genai.Client): The GenAI client instance.
        model_name (str): The name of the model to use for content generation.
        prompt (str): The prompt to send to the model.
        max_retries (int): Maximum number of retry attempts for transient errors.
        retry_delay (int): Delay between retries in seconds.

    Returns:
        Any
        The response returned by ``genai_client.generate()``.

    Raises:
        httpx.RemoteProtocolError: If the server disconnects unexpectedly.
        httpx.HTTPError: For other HTTP-related errors.
        GoogleAPIError: For errors specific to the Google API.
    """
    answer = None

    for attempt in range(1, max_retries + 1):
        try:
            answer = genai_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": Presentation,
                },
            )
            return answer

        except httpx.RemoteProtocolError as e:
            print(f"[Attempt {attempt}] Server disconnected: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                raise  # re-raise if out of retries

        except httpx.HTTPError as e:
            print(f"[Attempt {attempt}] HTTP error: {e}")
            raise  # you might not want to retry on all HTTP errors

        except GoogleAPIError as e:
            print(f"Google API error: {e}")
            raise

        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    raise RuntimeError("generate_with_retry exhausted retries without returning")


def generate_slides_with_nanobanana(
    presentation,
    out_dir: str = "generated_slides",
    model: str = "gemini-2.5-flash-image",
):
    """
    Generate slide images from a Presentation Pydantic using Nano Banana.
    Returns list of generated file paths.
    """

    slides_dir = os.path.join(out_dir, "generated_slides")
    os.makedirs(slides_dir, exist_ok=True)

    generated_files = []

    for idx, slide in enumerate(presentation["slides"], start=1):

        # --- Build prompt ---
        prompt = build_prompt_for_slide(presentation, slide)
        parts = [{"text": prompt}]

        # Add reference image if present
        image_info = slide.get("image")
        if image_info and image_info.get("path"):
            try:
                with open(image_info["path"], "rb") as f:
                    parts.insert(0, {"mime_type": "image/png", "data": f.read()})
            except FileNotFoundError:
                print(f"⚠ Reference image not found: {image_info['path']}")

        # --- Generate image ---
        print(f"▶ Generating slide {idx}: {slide.get('type', 'unknown')}")

        response = client.models.generate_content(
            model=model, contents=[{"role": "user", "parts": parts}]
        )

        # --- Decode inline data ---
        image_bytes = None
        for part in response.parts:
            if hasattr(part, "inline_data") and getattr(part.inline_data, "data", None):
                image_bytes = base64.b64decode(part.inline_data.data)
                break

        if not image_bytes:
            raise RuntimeError(f"❌ No image returned for slide {idx}")

        # --- Save output image ---
        filename = out_dir / f"slide_{idx:02d}.png"
        with open(filename, "wb") as f:
            f.write(image_bytes)

        print(f"✔ Saved {filename}")
        generated_files.append(str(filename))

    return generated_files


def build_prompt_for_slide(presentation, slide):
    """
    Builds a high-quality prompt for Nano Banana (Gemini Flash)
    given your structured schema.
    """

    base = f"""
Create a clean, professional presentation slide illustration.
Presentation title: "{presentation["title"]}"
Author: {presentation["author"]}

Slide type: {slide["type"]}
"""

    # Slide type specific details
    if slide["type"] == "title":
        content_text = (
            f'Title slide: "{presentation["title"]}" by {presentation["author"]}.'
        )
    else:
        content_text = f'Slide title: {slide["title"] or ""}\n'

    # Content formatting
    if slide.get("content_format") == "itemize":
        bullet_list = "\n".join([f"• {c}" for c in slide.get("content", [])])
    else:
        bullet_list = "\n".join(slide.get("content", []))

    # Layout directive

    layout_hint = ""
    layout_type = slide.get("layout", "")

    if layout_type == "text_only":
        layout_hint = "Layout: text-only, no illustration except subtle background."
    elif layout_type == "two_column":
        layout_hint = "Layout: two-column with image + text."
    elif layout_type == "single_image":
        layout_hint = "Layout: single large illustration."

    # Orientation hint
    image_info = slide.get("image")
    if image_info and image_info.get("orientation"):
        layout_hint += f"\nImage orientation: {image_info['orientation']}."

    return (
        base
        + "\n"
        + content_text
        + "\nMain slide content:\n"
        + bullet_list
        + "\n\n"
        + layout_hint
        + "\nOutput a single clean 16:9 illustration.\n"
    )
