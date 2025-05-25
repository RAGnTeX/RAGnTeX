"""Module to handle file uploads via UI."""

from pathlib import Path
import shutil
from ..telemetry.logging_utils import Logger

LOGGER = Logger.get_logger()


def upload_files(files: list) -> tuple[str, list[str]]:
    """Upload files and save them in the temporary directory.
    Args:
        files (list): List of file-like objects to be uploaded.
    Returns:
        str: Message indicating the result of the upload operation.
        list[str]: List of saved file paths.
    """
    if not files:
        return "No files selected."

    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]  # utils → src → PROJECT ROOT
    UPLOAD_DIR = project_root / "uploaded_docs"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    messages = []
    saved_paths = []

    for file in files:
        try:
            temp_path = Path(file.name)
            file_name = temp_path.name
            target_path = UPLOAD_DIR / file_name

            if not temp_path.exists():
                messages.append(f"❌ File not found: {file_name} (already uploaded?)")
                continue

            if target_path.exists():
                messages.append(f"⚠️ File already exists: {file_name} — skipped.")
            else:
                shutil.move(str(temp_path), str(target_path))
                messages.append(f"✅ Uploaded: {file_name}")
                LOGGER.info("Uploaded file %s to %s", file_name, UPLOAD_DIR)

            saved_paths.append(str(target_path))

        except Exception as e:
            LOGGER.error(f"Error uploading {file_name}: {e}")
            messages.append(f"❌ Error uploading {file_name}: {e}")

    return "\n".join(messages), saved_paths
