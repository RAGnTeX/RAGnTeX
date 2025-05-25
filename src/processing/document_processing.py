"""Module handling PDF document processing and content extraction."""

import re
import os
from pathlib import Path
import fitz

from .images_processing import extract_images, extract_vector
from ..telemetry import Logger

LOGGER = Logger.get_logger()


def extract_pdf_content(pdf_path: str):
    doc = fitz.open(pdf_path)
    pdf = os.path.splitext(os.path.basename(pdf_path))[0]

    text = ""
    figs = []
    for page_num, page in enumerate(doc):
        # Parse the text
        text = " ".join([text, page.get_text().strip()])

        # Extract images
        figs += extract_images(pdf, doc, page, page_num)

        # Extract vector graphics
        figs += extract_vector(pdf, doc, page, page_num)

    # Format the metadata
    metas = {"num_images": len(figs), "pdf_path": pdf_path}

    return text, figs, metas


def process_documents(pdf_files):
    documents = []
    metadatas = []

    for pdf_path in pdf_files:
        text, imgs, metas = extract_pdf_content(pdf_path)

        documents.append(text)

        # Format images
        images_info = []
        for i, img in enumerate(imgs, start=1):
            caption = img.get("caption")
            caption_str = str(caption) if caption is not None else ""
            img_name = img["name"]
            img_ratio = img["ratio"]
            full_path = f"gfx/{img_name}"

            cleaned_caption = re.sub(
                r"^(fig(?:ure)?\.?\s*\d+\.\s*)", "", caption_str, flags=re.IGNORECASE
            ).strip()
            caption = cleaned_caption if cleaned_caption else "None"

            images_info.append(
                f'{{"path": "{full_path}", "caption": "{caption}", "orientation": "{img_ratio}"}}'
            )

        images_passage = "\n".join(images_info)

        # Format metadata
        fixed_metadata = {
            "num_images": metas.get("num_images"),
            "pdf_path": metas.get("pdf_path"),
            "images_passage": images_passage,
        }
        metadatas.append(fixed_metadata)

    return documents, metadatas


def delete_uploaded_files(uploaded_files):
    """Delete uploaded files after processing."""
    for file in uploaded_files:
        try:
            path = Path(file)
            if path.exists():
                path.unlink()  # Delete the file
                LOGGER.info(f"Deleted file: {file}")
            else:
                LOGGER.warning(f"File not found for deletion: {file}")
            LOGGER.info("🧹 Cleaned up uploaded files.")
        except Exception as e:
            LOGGER.warning(f"Failed to delete {file}", exc_info=e)
