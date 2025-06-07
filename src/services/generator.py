"""Module to put it all together and manage the generation of a presentation."""

from pathlib import Path

# from datetime import datetime
from ..database import ingest_files_to_db, retrive_files_from_db
from ..telemetry import Logger, generate_with_trace, traced_block
from ..processing import get_prompt, create_output_folder
from . import client
from ..compilation import compile_presentation
from ..processing import delete_uploaded_files, find_used_fgx


LOGGER = Logger.get_logger()


def generate_presentation(theme, color, topic, uploaded_files) -> tuple[str, str, str]:
    """Main function to generate a presentation based on the provided theme, color, and topic.
    Args:
        theme (str): The theme of the presentation, chosen by user via UI, defaults to "default".
        color (str): The color scheme for the presentation, chosen by user via UI,
        defaults to "default".
        topic (str): The topic of the presentation, set by user via UI, defaults to "default".
        uploaded_files (list): List of file paths to be ingested, provided by user via UI.
    Returns:
        tuple: A 3-element tuple:
            - str: Success message.
            - str: Path to the generated presentation.
            - str: Placeholder for the output viewer.
    """
    with traced_block(
        "📽️ generate_presentation",
        input_theme=theme,
        input_color=color,
        input_topic=topic,
        file_count=len(uploaded_files),
    ) as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        ingest_files_to_db(uploaded_files)

        [documents], [metadatas] = retrive_files_from_db(topic)
        # print("metadatas retrieved:", metadatas)

        prompt = get_prompt(theme, color)

        for passage, metas in zip(documents, metadatas):
            passage_oneline = passage.replace("\n", " ")
            images_passage = metas["images_passage"]

            prompt += f"PASSAGE: {passage_oneline}\n"
            prompt += f"IMAGES: {images_passage}\n"
            # print(f"passage_oneline = {passage_oneline}")
            # print(f"images_passage = {images_passage}")

        work_dir = create_output_folder()
        # Generate the presentation code
        model_name = "gemini-2.0-flash"
        LOGGER.info("⭐️ Generating response...")
        answer = generate_with_trace(client, model_name, prompt)
        LOGGER.info("🎲 Generated the response using: %s", model_name)

        find_used_fgx(answer, work_dir, metadatas)
        compile_presentation(answer.text, work_dir)

        delete_uploaded_files(uploaded_files)
        output_path = Path(work_dir + "/presentation.pdf")
        return "Presentation generated successfully!", str(output_path), "", trace_id
