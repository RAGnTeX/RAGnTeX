"""Module to handle file uploads and downloads via UI."""

import re
import shutil
import zipfile
from pathlib import Path

from ..database import ingest_files_to_db
from ..telemetry.logging_utils import Logger

LOGGER = Logger.get_logger()


def upload_files(files: list, session_id: str) -> tuple[str, list[str]]:
    """Upload files and save them in the temporary directory.
    Args:
        files (list): List of file-like objects to be uploaded.
        session_id (str): Unique identifier for the current session.
    Returns:
        str: Message indicating the result of the upload operation.
        list[str]: List of saved file paths.
    """
    if not files:
        return "❌ No new files selected.", []

    upload_dir = Path.cwd() / "tmp" / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    messages = []
    saved_paths = []

    for file in files:
        try:
            temp_path = Path(file.name)
            # Prepare the safe file name
            safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", temp_path.stem)
            safe_name = re.sub(r"_+", "_", safe_name)
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
        failed = ingest_files_to_db(saved_paths, session_id)
        if failed:
            messages.append(
                f"⚠️ Failed to process files: {', '.join(Path(f).name for f in failed)}"
            )
            LOGGER.warning(
                "⚠️ Failed to process files: %s", ", ".join(Path(f).name for f in failed)
            )
        else:
            messages.append("🛠️ All files processed successfully!")
            LOGGER.info("🛠️ All files processed successfully!")

    return "\n".join(messages), saved_paths


def download_files(compilation_status, folder_path, session_id) -> list[str]:
    """Prepare downloadable zip archive from the specified folder path.

    Args:
        compilation_status (str): Status of the compilation.
        folder_path (str): Path to the folder containing files to be zipped.
        session_id (str): Unique identifier for the current session.

    Returns:
        Optional[str]: Path to the created zip archive or None if folder_path is empty.
    """

    if not folder_path:
        return []

    folder = Path(folder_path)
    base_dir = Path.cwd() / "tmp" / session_id

    all_zips = [base_dir / "presentation.zip"]
    all_zips += sorted(base_dir.glob("presentation_*.zip"))
    all_zips = [str(p) for p in all_zips if p.exists() and p.is_file()]
    if compilation_status == "":
        return all_zips

    if all_zips:
        last_file = Path(all_zips[-1]).name
        match = re.match(r"presentation_(\d+)\.zip", last_file)
        if match:
            next_num = int(match.group(1)) + 1
        else:
            next_num = 2
        zip_path = base_dir / f"presentation_{next_num}.zip"
    else:
        zip_path = base_dir / "presentation.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add gfx folder
        gfx_folder = folder / "gfx"
        if gfx_folder.exists() and gfx_folder.is_dir():
            for file in gfx_folder.rglob("*"):
                if file.is_file():
                    arcname = Path("presentation") / file.relative_to(folder)
                    zipf.write(file, arcname=arcname)
        # Add tex and pdf files
        for filename in ["presentation.tex", "presentation.pdf"]:
            file_path = folder / filename
            if file_path.exists() and file_path.is_file():
                arcname = Path("presentation") / filename
                zipf.write(file_path, arcname=arcname)
    LOGGER.info("📦 Created zip archive at %s", zip_path)

    all_zips.append(str(zip_path))

    return all_zips


def delete_files(session_id: str) -> None:
    """Delete all files in the specified session's temporary directory.
    Args:
        session_id (str): Unique identifier for the current session.
    """

    upload_dir = Path.cwd() / "tmp" / session_id

    if not upload_dir.exists():
        return

    try:
        shutil.rmtree(upload_dir)
        LOGGER.info("🗑️ Deleted folder: %s", upload_dir)
        return
    except Exception as e:
        LOGGER.error("❌ Error deleting: %s", upload_dir, exc_info=e)
        return
