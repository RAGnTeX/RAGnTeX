import json
from .database import db, embed_fn
from ..telemetry import Logger, traced_block

LOGGER = Logger.get_logger()


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
    with traced_block("🔎 retrieve_documents") as span:
        span.set_attribute("input.query_oneline", query_oneline)
        n_yelded_docs = 2
        result = db.query(query_texts=[query_oneline], n_results=n_yelded_docs)
        span.set_attribute("output.n_results", n_yelded_docs)
        span.set_attribute("output.metadatas", json.dumps(result["metadatas"]))
        [documents] = result["documents"]
        [metadatas] = result["metadatas"]

        return [documents], [metadatas]
