from pathlib import Path
import shutil
from .logging_utils import Logger

LOGGER = Logger.get_logger()


def upload_files(files):
    # File: src/utils/app.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[2]  # utils → src → PROJECT ROOT
    UPLOAD_DIR = project_root / "uploaded_docs"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    for file in files:

        # Temporary path where Gradio stores the file
        temp_path = file.name
        file_name = Path(file.name).name
        LOGGER.info("Uploading file: %s", file_name)

        # Define where you want to save the file
        filepath = UPLOAD_DIR / file_name

        # Move the temporary file to your target location
        shutil.move(temp_path, filepath)

        # Add the file path to the uploaded files list
        # uploaded_files.append(filepath)

        LOGGER.info("Uploading file %s to folder %s", file_name, UPLOAD_DIR)
