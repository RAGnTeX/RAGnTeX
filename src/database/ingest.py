# database/ingest.py
from pathlib import Path
from .database import db
from ..utils import Logger
from ..processing import process_documents

LOGGER = Logger.get_logger()


def ingest_files_to_db(pdf_files) -> None:
    """Add new files to the database if they are not yet there.
    Args:
        pdf_files (list): List of PDF files to be ingested.
    """
    print("pdf_files", pdf_files)
    # Get all the existing entries and extract the known filenames
    all_entries = db.get(include=["metadatas"])
    existing_pdfs = set(
        meta.get("source_pdf")
        for meta in all_entries["metadatas"]
        if meta.get("source_pdf")
    )

    # Filter out already ingested PDFs
    new_pdfs = [file for file in pdf_files if Path(file).name not in existing_pdfs]

    if not new_pdfs:
        LOGGER.info("No new PDFs to ingest. Skipping ingestion.")
        return

    # Process new files only
    documents, metadatas = process_documents(new_pdfs)

    LOGGER.info(f"Adding {len(new_pdfs)} new PDFs to the database...")
    if documents:
        db.add(
            documents=documents,
            ids=[str(i) for i in range(len(documents))],
            metadatas=metadatas,
        )
    LOGGER.info("Documents ingested successfully.")
