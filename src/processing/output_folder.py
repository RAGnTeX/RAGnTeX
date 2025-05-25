"""Module to create an output folder for saving results."""

import os
from pathlib import Path
from datetime import datetime
from ..telemetry import Logger

LOGGER = Logger.get_logger()


def create_output_folder() -> str:
    """Create a new folder where the output will be saved.
    Returns:
        str: Path to the newly created output folder.
    """
    LOGGER.info("💾 Creating new subfolder...")
    cwd = Path.cwd()
    one_level_up = cwd.parent
    base_path = one_level_up / "output"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    work_dir = os.path.join(base_path, timestamp)
    print("work_dir", work_dir)
    os.makedirs(work_dir, exist_ok=False)
    LOGGER.info("📁 Created folder: %s", work_dir)
    return work_dir
