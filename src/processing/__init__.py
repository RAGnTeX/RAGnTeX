"""This module initializes the document processing package."""

from .document_processing import delete_uploaded_files, process_documents
from .images_processing import find_used_gfx, save_pdf_figures, save_pdf_images
from .output_folder import create_output_folder
from .prompt import get_prompt

__all__ = [
    "process_documents",
    "delete_uploaded_files",
    "save_pdf_images",
    "save_pdf_figures",
    "find_used_gfx",
    "create_output_folder",
    "get_prompt",
]
