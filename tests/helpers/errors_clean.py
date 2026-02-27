import re
from simple_error_log.errors import Errors


def errors_clean_all(errors: Errors) -> list[dict]:
    result = errors.to_dict(0)
    for item in result:
        item = _fix_timestamp(item)
        item = _remove_file_paths(item)
    return result


def error_clean(errors: Errors, index=0) -> dict:
    result = errors._items[index].to_dict()
    result = _remove_file_paths(result)
    return _fix_timestamp(result)


def _fix_timestamp(data: dict) -> dict:
    timestamp_pattern = r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})\.(\d{6})"
    if "timestamp" in data:
        data["timestamp"] = re.sub(
            timestamp_pattern, "YYYY-MM-DD HH:MM:SS.nnnnnn", data["timestamp"]
        )
    return data


def _relative_path(path: str) -> str:
    for marker in ["src/", "tests/"]:
        idx = path.find(marker)
        if idx != -1:
            return path[idx:]
    parts = path.split("site-packages/")
    if len(parts) >= 2:
        return parts[-1]
    return path.split("/")[-1]


def _clean_traceback_paths(error_text: str) -> str:
    # Clean 'File "path"' patterns
    file_pattern = r'File\s+"([^"]+)"'

    def clean_file_path(match):
        cleaned = _relative_path(match.group(1))
        return f'File "{cleaned}"'

    result = re.sub(file_pattern, clean_file_path, error_text)

    # Clean bare absolute paths (e.g. /Users/.../tests/foo.py, line 52)
    abs_pattern = r"(?<=\s)(/\S+?)(?=,)"

    def clean_abs_path(match):
        return _relative_path(match.group(1))

    result = re.sub(abs_pattern, clean_abs_path, result)
    return result


def _remove_file_paths(data: dict) -> dict:
    if "message" in data:
        data["message"] = _clean_traceback_paths(data["message"])
    return data
