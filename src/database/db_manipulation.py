"""Module for adding and getting PDF files to/from the database."""

from typing import List, Mapping, Union

from langfuse.decorators import langfuse_context, observe

from ..processing import process_documents
from ..telemetry import Logger
from .database import chroma_client, embed_fn

LOGGER = Logger.get_logger()


@observe(name="𝌊 ingest_files_to_db")
def ingest_files_to_db(pdf_files, session_id) -> list[str]:
    """Add new files to the database if they are not yet there.
    Args:
        pdf_files (list): List of PDF files to be ingested.
        session_id (str): Unique identifier for the current session.
    """
    # Get or create the database collection
    db = chroma_client.get_or_create_collection(name=session_id, embedding_function=embed_fn)

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
        return []

    # Process new files only
    documents, metadatas, failed = process_documents(new_pdfs)

    LOGGER.info("➕ Adding %d new PDFs to the database...", len(new_pdfs))
    if documents:
        db.add(
            documents=documents,
            ids=[str(i) for i in range(len(documents))],
            metadatas=metadatas,
        )
    LOGGER.info("✅ Documents ingested successfully.")

    return failed


Metadata = Mapping[str, Union[str, int, float, bool]]
DocumentsBatch = List[List[str]]
MetadataBatch = List[List[Metadata]]


@observe(name="🔍 retrieve_files_from_db")
def retrive_files_from_db(topic: str, session_id: str) -> tuple[DocumentsBatch, MetadataBatch]:
    """Retrieve relevant documents from the database based on the provided topic.
    Args:
        topic (str): The topic for which to retrieve documents.
        session_id (str): Unique identifier for the current session.
    Returns:
        tuple: A 2-element tuple:
            - list[str]: List of retrieved documents.
            - list[dict]: List of metadata associated with the documents.
    """
    # Get or create the database collection
    db = chroma_client.get_or_create_collection(name=session_id, embedding_function=embed_fn)
    if not db:
        LOGGER.error("❌ Database collection not found or could not be created.")
        return [], []

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


def clean_db(session_id: str) -> None:
    """Clean the database collection for the given session ID.
    Args:
        session_id (str): Unique identifier for the current session.
    """
    db = chroma_client.get_or_create_collection(name=session_id, embedding_function=embed_fn)
    if db:
        chroma_client.delete_collection(name=session_id)
        LOGGER.info("🗑️ Cleaning database for session ID: %s", session_id)
    else:
        LOGGER.warning("❌ Database collection not found for session ID: %s", session_id)