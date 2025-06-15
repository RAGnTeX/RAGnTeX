"""Module to put it all together and manage the generation of a presentation."""

from langfuse.decorators import langfuse_context, observe

from src.compilation import compile_presentation, json_to_tex, replace_unicode_greek

# from datetime import datetime
from src.database import retrive_files_from_db
from src.processing import create_output_folder, find_used_gfx
from src.services import Presentation, build_prompt, client
from src.telemetry import Logger

LOGGER = Logger.get_logger()


@observe(name="🧑‍🎨 generate_presentation")
def generate_presentation(theme, color, topic, session_id) -> tuple[str, str, str]:
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

    trace_id = langfuse_context.get_current_trace_id()

    [documents], [metadatas] = retrive_files_from_db(topic, session_id)

    prompt = build_prompt(documents, metadatas)

    work_dir = create_output_folder(session_id)
    # Generate the presentation code
    model_name = "gemini-2.0-flash"
    LOGGER.info("⭐️ Generating response...")
    answer = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": Presentation,
        },
    )
    langfuse_context.update_current_observation(
        output={
            "model_name": model_name,
            "prompt_length": len(prompt),
            "output.response": answer.text,
        }
    )
    LOGGER.info("🎲 Generated the response using: %s", model_name)

    find_used_gfx(answer, work_dir, metadatas)
    latex_code = json_to_tex(answer.text, theme, color)
    latex_code = replace_unicode_greek(latex_code)
    compilation_status = compile_presentation(latex_code, work_dir)

    if compilation_status:
        return compilation_status, trace_id, work_dir
    return "❌ Unknown critial error. Please try again later.", trace_id, work_dir
