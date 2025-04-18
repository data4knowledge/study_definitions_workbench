import os
from pathlib import Path
from d4k_ms_base.logger import application_logger

_file_path = os.path.realpath(__file__)
static_path = f"{str(Path(_file_path).parents[1])}/static"
application_logger.info(f"Status dir set to '{static_path}'")
