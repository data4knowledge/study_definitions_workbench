import os
from pathlib import Path
from d4kms_generic import application_logger

_file_path = os.path.realpath(__file__)
static_path = f"{str(Path(_file_path).parents[1])}/static"
application_logger.info(f"Status dir set to '{static_path}'")

