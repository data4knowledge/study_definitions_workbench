"""STRATO hosting patch: containment/validation helpers for file downloads.

Guards the FileResponse sinks flagged by Snyk Code (python/PT). Kept in one
module so the patch is easy to re-apply on upstream upgrades.
"""

import os
import re

from fastapi import HTTPException

from app.configuration.configuration import application_configuration

_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:\-]{1,128}$")


def safe_identifier(value: str) -> str:
    """Reject identifiers (e.g. USDM ids) containing path separators or odd characters."""
    if not isinstance(value, str) or not _IDENTIFIER.match(value) or ".." in value:
        raise HTTPException(status_code=404, detail="Not found")
    return value


def safe_data_path(path: str) -> str:
    """Return the resolved path only if it lies inside the data files directory."""
    root = os.path.realpath(application_configuration.data_file_path)
    resolved = os.path.realpath(path)
    if os.path.commonpath([resolved, root]) != root:
        raise HTTPException(status_code=404, detail="Not found")
    return resolved
