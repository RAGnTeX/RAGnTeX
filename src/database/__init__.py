"""This module initializes the database package."""

from .database import db, embed_fn
from .db_manipulation import ingest_files_to_db, retrive_files_from_db

__all__ = ["db", "embed_fn", "ingest_files_to_db", "retrive_files_from_db"]
