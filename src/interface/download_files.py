import zipfile
from pathlib import Path
from ..telemetry.logging_utils import Logger

LOGGER = Logger.get_logger()


def download_files(folder_path) -> str:
    """Prepare downloadable zip archive from the specified folder path."""

    if not folder_path:
        return "No folder path provided."
    
    folder = Path(folder_path)
    zip_path = Path.cwd() / "presentation.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in folder.rglob('*'):
            if file.is_file() and file != zip_path:
                arcname = Path("presentation") / file.relative_to(folder)
                zipf.write(file, arcname=arcname)
    LOGGER.info("📦 Created zip archive at %s", zip_path)

    return str(zip_path)
