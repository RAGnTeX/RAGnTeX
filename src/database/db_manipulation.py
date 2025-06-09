"""Module for adding and getting PDF files to/from the database."""

from typing import Mapping, Union, List
from langfuse.decorators import langfuse_context, observe

from .database import db, embed_fn
from ..telemetry import Logger
from ..processing import process_documents

LOGGER = Logger.get_logger()


@observe(name="𝌊 ingest_files_to_db")
def ingest_files_to_db(pdf_files) -> None:
    """Add new files to the database if they are not yet there.
    Args:
        pdf_files (list): List of PDF files to be ingested.
    """
    # Get all the existing entries and extract the known filenames
    all_entries = db.get(include=["metadatas"]) or []

    if not all_entries:
        LOGGER.info("📂 No existing entries in the database. Ingesting all PDFs.")

    existing_pdfs = set(
        meta.get("pdf_path")
        for meta in all_entries["metadatas"]  # type: ignore[union-attr]
        if meta.get("pdf_path")
    )

    # Filter out already ingested PDFs
    new_pdfs = [file for file in pdf_files if file not in existing_pdfs]

    if not new_pdfs:
        LOGGER.info("📂 No new PDFs to ingest. Skipping ingestion.")
        return

    # Process new files only
    documents, metadatas = process_documents(new_pdfs)

    LOGGER.info("➕ Adding %d new PDFs to the database...", len(new_pdfs))
    if documents:
        db.add(
            documents=documents,
            ids=[str(i) for i in range(len(documents))],
            metadatas=metadatas,
        )
    LOGGER.info("✅ Documents ingested successfully.")


Metadata = Mapping[str, Union[str, int, float, bool]]
DocumentsBatch = List[List[str]]
MetadataBatch = List[List[Metadata]]


@observe(name="🔍 retrieve_files_from_db")
def retrive_files_from_db(topic: str) -> tuple[DocumentsBatch, MetadataBatch]:
    """Retrieve relevant documents from the database based on the provided topic.
    Args:
        topic (str): The topic for which to retrieve documents.
    Returns:
        tuple: A 2-element tuple:
            - list[str]: List of retrieved documents.
            - list[dict]: List of metadata associated with the documents.
    """
    LOGGER.info("🔍 Retrieving relevant documents...")
    embed_fn.document_mode = False
    query_oneline = topic.replace("\n", " ")

    n_yelded_docs = 2
    result = db.query(query_texts=[query_oneline], n_results=n_yelded_docs)
    langfuse_context.update_current_observation(
        output={
            "input.query_oneline": query_oneline,
            "output.n_results": n_yelded_docs,
            "output.metadatas": result["metadatas"],
        }
    )
    [documents] = result.get("documents") or [[]]
    [metadatas] = result.get("metadatas") or [[]]

    return [documents], [metadatas]
