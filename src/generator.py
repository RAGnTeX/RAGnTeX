"""Module to put it all together and manage the generation of a presentation."""

from dataclasses import dataclass
from typing import Optional

from langfuse.decorators import langfuse_context, observe

from src.compilation import (
    compile_presentation,
    json_to_tex,
    replace_unicode_greek,
    escape_latex_special_chars,
)

# from datetime import datetime
from src.database import retrive_files_from_db
from src.processing import create_output_folder, find_used_gfx
from src.services import build_prompt, client, generate_with_retry
from src.telemetry import Logger

LOGGER = Logger.get_logger()


@dataclass
class PresentationConfig:
    """Configuration for the presentation generation."""

    model_name: str = "gemini-2.0-flash"
    aspect_ratio: str = "16:9"
    theme: str = "default"
    color_theme: str = "default"
    topic: str = ""


@observe(name="🧑‍🎨 generate_presentation")
def generate_presentation(
    config_dict, session_id
) -> tuple[str, Optional[str], Optional[str]]:
    """Main function to generate a presentation based on the provided theme, color, and topic.

    Args:
        config_dict (dict): Configuration dictionary containing:
            - model_name (str): Name of the model to use for generation.
            - aspect_ratio (str): Aspect ratio for the presentation, e.g., "16:9", "4:3".
            - theme (str): Beamer theme to use.
            - color_theme (str): Beamer color theme to use.
            - topic (str): Topic of the presentation.
        session_id (str): Unique identifier for the current session.

    Returns:
    tuple:
        A 3-element tuple containing:
        - str: Status message (success or error).
        - Optional[str]: Trace ID for telemetry purposes, or None if unavailable.
        - Optional[str]: Path to the presentation folder, or None if unavailable.
    """
    # Cast dict to dataclass
    try:
        config = PresentationConfig(**config_dict)
    except TypeError as e:
        # Handle missing or extra keys gracefully
        return f"Config error: {str(e)}", None, None

    trace_id = langfuse_context.get_current_trace_id()

    [documents], [metadatas] = retrive_files_from_db(config.topic, session_id)

    if not documents or not metadatas:
        LOGGER.error("❌ No documents found for the topic: %s", config.topic)
        return "❌ No documents found for the given topic.", trace_id, None

    prompt = build_prompt(documents, metadatas, config.aspect_ratio)

    # Generate the presentation code
    model_name = config.model_name
    LOGGER.info("⭐️ Generating response...")
    try:
        answer = generate_with_retry(client, model_name, prompt)
    except Exception as e:
        LOGGER.error("❌ Gemini is not reponding: %s", str(e))
        return f"❌ Gemini error: {str(e)}", trace_id, None

    langfuse_context.update_current_observation(
        output={
            "model_name": model_name,
            "session_id": session_id,
            "aspect_ratio": config.aspect_ratio,
            "prompt_length": len(prompt),
            "output.response": answer.text,
        }
    )
    LOGGER.info("🎲 Generated the response using: %s", model_name)

    work_dir = create_output_folder(session_id)

    find_used_gfx(answer, work_dir, metadatas)
    latex_code = json_to_tex(
        answer.text, config.theme, config.color_theme, config.aspect_ratio
    )
    latex_code = replace_unicode_greek(latex_code)
    latex_code = escape_latex_special_chars(latex_code)
    compilation_status = compile_presentation(latex_code, work_dir)

    if compilation_status:
        return compilation_status, trace_id, work_dir
    return "❌ Unknown critial error. Please try again later.", trace_id, work_dir
