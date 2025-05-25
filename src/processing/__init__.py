"""This module initializes the document processing package."""

from .document_processing import process_documents, delete_uploaded_files
from .images_processing import save_pdf_images, save_pdf_figures, find_used_fgx
from .output_folder import create_output_folder
from .prompt import get_prompt

__all__ = [
    "process_documents",
    "delete_uploaded_files",
    "save_pdf_images",
    "save_pdf_figures",
    "find_used_fgx",
    "create_output_folder",
    "get_prompt",
]
