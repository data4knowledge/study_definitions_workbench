import json

from d4k_ms_base.logger import application_logger

from app.configuration.configuration import application_configuration


def server_name(request) -> str:
    application_logger.info(
        f"Base URL used to obtain server name: '{request.base_url}'"
    )
    name = str(request.base_url)
    if "staging" in name:
        return "STAGING"
    elif "training" in name:
        return "TRAINING"
    elif "d4k-sdw" in name:
        return "PRODUCTION"
    elif "localhost" in name or "0.0.0.0" in name:
        return "DEVELOPMENT"
    elif "dnanexus.cloud" in name:
        return "PRISM"
    else:
        return name


def single_multiple() -> str:
    return "SINGLE" if application_configuration.single_user else "MULTIPLE"


def restructure_study_list(data: list[dict]) -> dict:
    """Transpose a per-study list of dicts into a dict of per-study tuples.

    ``data`` carries one entry per selected study, in column order, and an
    entry is ``None`` whenever the view could not be built for that study
    (e.g. ``DataView.title_page()`` returns ``None`` for a non-M11 import).
    Those studies still need a column, so the key set is the union over the
    dicts that do exist and a missing study contributes ``None`` in every
    row. Indexing ``None`` here used to raise "'NoneType' object is not
    subscriptable" whenever an M11 study was compared alongside a non-M11
    one.
    """
    keys = []
    for entry in data:
        if not entry:
            continue
        for k in entry.keys():
            if k not in keys:
                keys.append(k)
    return {k: tuple((d.get(k) if d else None) for d in data) for k in keys}


def convert_to_json(data) -> str:
    return json.dumps(data, indent=2)


def ellipsize(text, length: int = 30) -> str:
    """Truncate text for space-constrained UI (tab labels, pills,
    table cells) with a trailing ellipsis. Registered as the Jinja
    filter ``ellipsize``: ``{{ title | ellipsize }}`` or
    ``{{ title | ellipsize(20) }}``. Pair with a ``title`` attribute
    so the full text stays available on hover."""
    if text is None:
        return ""
    text = str(text)
    if len(text) <= length:
        return text
    return text[: length - 1].rstrip() + "…"
