from google.api_core import retry
from google.genai import types
from google import genai
from chromadb import Documents, EmbeddingFunction, Embeddings
import chromadb

from ..services import client

# Define a helper to retry when per-minute quota is reached.
is_retriable = lambda e: (isinstance(e, genai.errors.APIError) and e.code in {429, 503})


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.document_mode = True

    @retry.Retry(predicate=is_retriable)
    def __call__(self, input: Documents) -> Embeddings:
        if self.document_mode:
            embedding_task = "retrieval_document"
        else:
            embedding_task = "retrieval_query"

        response = client.models.embed_content(
            model="models/text-embedding-004",
            contents=input,
            config=types.EmbedContentConfig(
                task_type=embedding_task,
            ),
        )
        return [e.values for e in response.embeddings]


DB_NAME = "ragntex"

embed_fn = GeminiEmbeddingFunction()
embed_fn.document_mode = True

chroma_client = chromadb.Client()
# chroma_client.delete_collection(DB_NAME)
db = chroma_client.get_or_create_collection(name=DB_NAME, embedding_function=embed_fn)
