"""Initialize and export a GenAI client using the provided Google API key."""

import os
import time
import httpx
from google.api_core.exceptions import GoogleAPIError
from dotenv import load_dotenv
from google import genai

from .output_schema import Presentation

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)


def generate_with_retry(
    client: genai.Client,
    model_name: str,
    prompt: str,
    max_retries: int = 3,
    retry_delay: int = 2,
):

    answer = None

    for attempt in range(1, max_retries + 1):
        try:
            answer = client.models.generate_content(
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
