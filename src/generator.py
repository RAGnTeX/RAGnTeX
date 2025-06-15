"""Module to put it all together and manage the generation of a presentation."""

from dataclasses import dataclass

from langfuse.decorators import langfuse_context, observe

from src.compilation import compile_presentation, json_to_tex

# from datetime import datetime
from src.database import retrive_files_from_db
from src.processing import create_output_folder, find_used_gfx
from src.services import Presentation, build_prompt, client, generate_with_retry
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
def generate_presentation(config_dict, session_id) -> tuple[str, str, str]:
    """Main function to generate a presentation based on the provided theme, color, and topic.
    Args:
        theme (str): The theme of the presentation, chosen by user via UI, defaults to "default".
        color (str): The color scheme for the presentation, chosen by user via UI,
        defaults to "default".
        topic (str): The topic of the presentation, set by user via UI, defaults to "default".
        session_id (str): Unique identifier for the current session.
    Returns:
        tuple: A 3-element tuple:
            - str: Success message.
            - str: Trace ID for telemetry purposes.
            - str: Path to the presentation folder.
    """
    # Cast dict to dataclass
    try:
        config = PresentationConfig(**config_dict)
    except TypeError as e:
        # Handle missing or extra keys gracefully
        return f"Config error: {str(e)}", None, None

    trace_id = langfuse_context.get_current_trace_id()

    [documents], [metadatas] = retrive_files_from_db(config.topic, session_id)

    prompt = build_prompt(documents, metadatas, config.aspect_ratio)

    work_dir = create_output_folder(session_id)
    # Generate the presentation code
    model_name = config.model_name
    LOGGER.info("⭐️ Generating response...")
    # answer = client.models.generate_content(
    #     model=model_name,
    #     contents=prompt,
    #     config={
    #         "response_mime_type": "application/json",
    #         "response_schema": Presentation,
    #     },
    # )
    try:
        answer = generate_with_retry(client, model_name, prompt)
    except Exception as e:
        LOGGER.error("❌ Gemini is not reponding: %s", str(e))
        return f"Gemini error: {str(e)}", trace_id, work_dir

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

    find_used_gfx(answer, work_dir, metadatas)
    latex_code = json_to_tex(
        answer.text, config.theme, config.color_theme, config.aspect_ratio
    )
    compilation_status = compile_presentation(latex_code, work_dir)

    # delete_uploaded_files(uploaded_files)

    if compilation_status:
        return compilation_status, trace_id, work_dir
    return "❌ Unknown critial error. Please try again later.", trace_id, work_dir
