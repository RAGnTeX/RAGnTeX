"""This module initializes the database package."""

from .database import chroma_client, embed_fn
from .db_manipulation import (clean_db, ingest_files_to_db,
                              retrive_files_from_db)

__all__ = ["chroma_client", "embed_fn", "ingest_files_to_db", "retrive_files_from_db", "clean_db"]
