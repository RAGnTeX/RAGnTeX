import json
from langfuse.decorators import langfuse_context, observe

from .database import db, embed_fn
from ..telemetry import Logger

LOGGER = Logger.get_logger()


@observe(name="🔍 retrieve_files_from_db")
def retrive_files_from_db(topic: str) -> tuple[list[str], list[dict]]:
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
    [documents] = result["documents"]
    [metadatas] = result["metadatas"]

    return [documents], [metadatas]
