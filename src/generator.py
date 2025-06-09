"""Module to put it all together and manage the generation of a presentation."""

from pathlib import Path
from langfuse.decorators import langfuse_context, observe

# from datetime import datetime
from src.database import retrive_files_from_db
from src.telemetry import Logger
from src.processing import get_prompt, create_output_folder
from src.services import client
from src.compilation import compile_presentation
from src.processing import delete_uploaded_files, find_used_gfx


LOGGER = Logger.get_logger()


@observe(name="🧑‍🎨 generate_presentation")
def generate_presentation(theme, color, topic) -> tuple[str, str, str]:
    """Main function to generate a presentation based on the provided theme, color, and topic.
    Args:
        theme (str): The theme of the presentation, chosen by user via UI, defaults to "default".
        color (str): The color scheme for the presentation, chosen by user via UI,
        defaults to "default".
        topic (str): The topic of the presentation, set by user via UI, defaults to "default".
    Returns:
        tuple: A 3-element tuple:
            - str: Success message.
            - str: Trace ID for telemetry purposes.
            - str: Path to the presentation folder.
    """

    trace_id = langfuse_context.get_current_trace_id()

    [documents], [metadatas] = retrive_files_from_db(topic)
    prompt = get_prompt(theme, color)

    for passage, metas in zip(documents, metadatas):
        passage_oneline = passage.replace("\n", " ")
        images_passage = metas["images_passage"]

        prompt += f"PASSAGE: {passage_oneline}\n"
        prompt += f"IMAGES: {images_passage}\n"

    work_dir = create_output_folder()
    # Generate the presentation code
    model_name = "gemini-2.0-flash"
    LOGGER.info("⭐️ Generating response...")
    answer = client.models.generate_content(model=model_name, contents=prompt)
    langfuse_context.update_current_observation(
        output={
            "model_name": model_name,
            "prompt_length": len(prompt),
            "output.response": answer.text,
        }
    )
    LOGGER.info("🎲 Generated the response using: %s", model_name)

    find_used_gfx(answer, work_dir, metadatas)
    compilation_status = compile_presentation(answer.text, work_dir)

    # delete_uploaded_files(uploaded_files)

    if compilation_status:
        return compilation_status, trace_id, work_dir
    else:
        return "❌ Unknown critial error. Please try again later.", trace_id, work_dir
