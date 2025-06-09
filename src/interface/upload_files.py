"""Module to handle file uploads via UI."""

import re
from pathlib import Path
import shutil
from ..telemetry.logging_utils import Logger
from ..database import ingest_files_to_db

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
        return "❌ No new files selected", []

    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]  # utils → src → PROJECT ROOT
    upload_dir = project_root / "uploaded_docs"
    upload_dir.mkdir(parents=True, exist_ok=True)

    messages = []
    saved_paths = []

    for file in files:
        try:
            temp_path = Path(file.name)
            # Prepare the safe file name
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', temp_path.stem)
            safe_name = re.sub(r'_+', '_', safe_name)
            file_name = f"{safe_name}{temp_path.suffix}"
            target_path = upload_dir / file_name

            if target_path.exists():
                messages.append(f"⚠️ File already exists: {file_name}")
                continue

            if not temp_path.exists():
                messages.append(f"❌ File not found: {file_name}")
                continue

            shutil.move(str(temp_path), str(target_path))
            messages.append(f"✅ Uploaded new file: {file_name}")
            LOGGER.info("📤 Uploaded file %s to %s", file_name, upload_dir)

            saved_paths.append(str(target_path))

        except (FileNotFoundError, PermissionError, shutil.Error, OSError) as e:
            LOGGER.error("❌ Error uploading %s", file_name, exc_info=e)
            messages.append(f"❌ Error uploading {file_name}: {e}")

    if saved_paths:
        ingest_files_to_db(saved_paths)

    return "\n".join(messages), saved_paths
