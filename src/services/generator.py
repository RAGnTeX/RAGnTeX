# services/generator.py
import os
import re
from pathlib import Path
from datetime import datetime
from ..database import db, embed_fn, ingest_files_to_db
from ..utils import Logger
from ..processing import get_prompt
from . import client
from ..compilation import CompilePresentation
from ..processing import save_pdf_images, save_pdf_figures

LOGGER = Logger.get_logger()


def generate_presentation(theme, color, topic, uploaded_files):
    print(f"Theme: {theme}, Color: {color}, Topic: {topic}")
    ingest_files_to_db(uploaded_files)

    LOGGER.info("Retrieving relevant documents...")
    embed_fn.document_mode = False

    query_oneline = topic.replace(
        "\n", " "
    )  # (Optional) For cleaner input in case of newlines
    result = db.query(query_texts=[query_oneline], n_results=2)
    [documents] = result["documents"]
    [metadatas] = result["metadatas"]

    prompt = get_prompt(theme, color)

    for passage, metas in zip(documents, metadatas):
        passage_oneline = passage.replace("\n", " ")
        images_passage = metas["images_passage"]

        prompt += f"PASSAGE: {passage_oneline}\n"
        prompt += f"IMAGES: {images_passage}\n"

    # Create a new subfolder
    LOGGER.info("💾 Creating new subfolder...")
    cwd = Path.cwd()
    one_level_up = cwd.parent
    base_path = one_level_up / "output"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    work_dir = os.path.join(base_path, timestamp)
    print("work_dir", work_dir)
    os.makedirs(work_dir, exist_ok=False)
    LOGGER.info("📁 Created folder: %s", work_dir)

    # Generate the presentation code
    model_name = "gemini-2.0-flash"
    LOGGER.info("⭐️ Generating response...")
    answer = client.models.generate_content(model=model_name, contents=prompt)
    LOGGER.info("🎲 Generated the response using: %s", model_name)
    # Create a subfolder for graphics

    graphics_dir = os.path.join(work_dir, "gfx")
    os.makedirs(graphics_dir, exist_ok=True)
    LOGGER.info("🌄 Images will be saved to: %s", graphics_dir)

    # Find images, which are used in the presentation
    pattern_img = re.compile(
        r"doc(?P<doc>[a-zA-Z0-9_]+)_page(?P<page>\d+)_img(?P<img>\d+)_hash(?P<hash>[a-fA-F0-9]{8})\.png"
    )
    matches_img = pattern_img.finditer(answer.text)

    req_imgs = []
    for match in matches_img:
        req_img = {
            "doc": match.group("doc"),
            "page": int(match.group("page")),
            "img": int(match.group("img")),
            "hash": match.group("hash"),
        }
        req_imgs.append(req_img)

    # Find figures, which are used in the presentation
    pattern_fig = re.compile(
        r"doc(?P<doc>[a-zA-Z0-9_]+)_page(?P<page>\d+)_fig(?P<fig>\d+)_hash(?P<hash>[a-fA-F0-9]{8})\.png"
    )
    matches_fig = pattern_fig.finditer(answer.text)

    req_figs = []
    for match in matches_fig:
        req_fig = {
            "doc": match.group("doc"),
            "page": int(match.group("page")),
            "fig": int(match.group("fig")),
            "hash": match.group("hash"),
        }
        req_figs.append(req_fig)

    # Save the required graphics
    for metadata in metadatas:
        save_pdf_images(metadata["pdf_path"], req_imgs, graphics_dir)
        save_pdf_figures(metadata["pdf_path"], req_figs, graphics_dir)

    LOGGER.info("Compiling presentation...")
    CompilePresentation(answer.text, work_dir)
    LOGGER.info("Presentation is ready!")
    # Clean up uploaded files
    print("uploaded_files", uploaded_files)
    for file in uploaded_files:
        try:
            path = Path(file)
            if path.exists():
                path.unlink()  # Delete the file
                LOGGER.info(f"Deleted file: {file}")
            else:
                LOGGER.warning(f"File not found for deletion: {file}")
        except Exception as e:
            LOGGER.warning(f"Failed to delete {file}", exc_info=e)

    LOGGER.info("🧹 Cleaned up uploaded files.")
    output_path = Path(work_dir + "/presentation.pdf")
    return "Presentation generated successfully!", str(output_path), ""
