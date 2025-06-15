"""Initialize and export a GenAI client using the provided Google API key."""

from __future__ import annotations

import os
import time
from typing import Any

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
