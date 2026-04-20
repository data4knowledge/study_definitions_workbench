"""Server-side formatters for validation findings (engine-agnostic).

Each ``to_*`` helper takes a list of finding dicts and returns a bytes /
string payload ready to stream as an HTTP response. Used by the shared
``/validate/download/{csv,json,md,xlsx}`` routes — one helper per
format keeps route code trivial and puts format logic in one place.

Findings here are produced by any of SDW's validation flows:
M11 docx (``M11Validator``), USDM v4 rules (``USDM4.validate``), and
USDM v4 CORE (``USDM4.validate_core``). The formatters don't care
which — each call site hands over a uniform row shape plus two
presentation hints (``kind`` and ``title``).

Row shape
---------

Authoritative row shape is the one produced by
:mod:`app.utility.finding_projections`:

    rule_id    — stable rule identifier
    severity   — "error" | "warning" | "info"
    section    — where in the document the finding applies
    element    — the specific element or attribute
    message    — human-readable finding text
    rule_text  — optional rule description (may be empty)
    path       — JSON/DOCX path for drill-down (may be empty)

Why server-side? Earlier iterations generated CSV / JSON / Markdown
in the browser via JS + Blob. Zero-JS became a project direction
(see docs/lessons_learned.md), so the generators moved here.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import date


# The canonical field set — matches the column set rendered in the
# shared ``validate/partials/results.html`` table so the download
# mirrors what the user sees on screen.
_FIELDS = (
    "rule_id",
    "severity",
    "section",
    "element",
    "message",
)

_MD_HEADERS = (
    "Rule",
    "Severity",
    "Section",
    "Element",
    "Message",
)


def default_filename(
    source_filename: str,
    extension: str,
    kind: str = "validation-findings",
) -> str:
    """Build a deterministic filename of the form
    ``{source-basename}-{kind}-{YYYY-MM-DD}.{extension}``.

    ``kind`` is the validator tag (e.g. ``"m11-findings"``,
    ``"usdm-core-findings"``, ``"usdm-rules-findings"``). Callers can
    pass any slug-safe string; the default is intentionally generic so
    call sites that don't care still produce a reasonable name.
    """
    base = (source_filename or "protocol").rsplit(".", 1)[0]
    return f"{base}-{kind}-{date.today().isoformat()}.{extension}"


def sanitise_filename(name: str, fallback: str) -> str:
    """Restrict to a safe subset so the name is inert in a
    Content-Disposition header. Returns the fallback on empty input."""
    cleaned = "".join(c for c in (name or "") if c.isalnum() or c in "-_. ")
    return cleaned or fallback


def to_csv(findings: list[dict]) -> bytes:
    """Serialise findings as UTF-8 CSV with a header row. RFC-4180
    escaping applies (DictWriter handles commas / quotes / newlines).
    """
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(_FIELDS), extrasaction="ignore")
    writer.writeheader()
    for finding in findings or []:
        row = _row_view(finding)
        writer.writerow({field: _stringify(row.get(field)) for field in _FIELDS})
    return buffer.getvalue().encode("utf-8")


def to_json(findings: list[dict]) -> bytes:
    """Pretty-printed JSON. Normalised to the canonical row shape so
    downstream consumers (diffing, archiving) see a stable key set
    regardless of which engine produced the findings."""
    normalised = [
        {field: _stringify(_row_view(finding).get(field)) for field in _FIELDS}
        for finding in findings or []
    ]
    return json.dumps(normalised, indent=2).encode("utf-8")


def to_markdown(
    findings: list[dict],
    source_filename: str,
    title: str = "Validation Findings",
) -> bytes:
    """A readable Markdown table with a heading and metadata. Useful for
    pasting into PRs, tickets, emails, or chat.

    ``title`` varies by validator (e.g. ``"M11 Validation Findings"``,
    ``"USDM v4 Rules Findings"``, ``"USDM v4 CORE Findings"``).
    """
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Source:** {source_filename or '(unknown)'}")
    lines.append(f"**Generated:** {date.today().isoformat()}")
    lines.append(f"**Findings:** {len(findings or [])}")
    lines.append("")
    if not findings:
        lines.append("_No findings._")
        return ("\n".join(lines) + "\n").encode("utf-8")
    lines.append("| " + " | ".join(_MD_HEADERS) + " |")
    lines.append("| " + " | ".join("---" for _ in _MD_HEADERS) + " |")
    for finding in findings:
        row = _row_view(finding)
        cells = [_md_cell(row.get(field)) for field in _FIELDS]
        lines.append("| " + " | ".join(cells) + " |")
    return ("\n".join(lines) + "\n").encode("utf-8")


def to_xlsx(
    findings: list[dict],
    source_filename: str,
    sheet_title: str = "Findings",
) -> io.BytesIO:
    """Render an openpyxl Workbook with two sheets: the findings
    table on the first sheet, and source-filename / generation-date
    metadata on the second. Returns an ``io.BytesIO`` ready to stream.

    ``sheet_title`` names the findings worksheet — e.g. ``"M11 Findings"``,
    ``"USDM Rules Findings"``, ``"USDM CORE Findings"``. Excel caps
    worksheet titles at 31 characters; callers should stay within that.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment

    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]  # Excel hard limit.

    headers = [
        ("Rule", 14),
        ("Severity", 10),
        ("Section", 24),
        ("Element", 28),
        ("Message", 70),
    ]
    for col_idx, (title, width) in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=title)
        cell.font = Font(bold=True)
        ws.column_dimensions[cell.column_letter].width = width

    for row_idx, finding in enumerate(findings or [], start=2):
        row = _row_view(finding)
        for col_idx, field in enumerate(_FIELDS, start=1):
            cell = ws.cell(
                row=row_idx, column=col_idx, value=_stringify(row.get(field))
            )
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    meta = wb.create_sheet("Source")
    meta["A1"] = "Source file"
    meta["A1"].font = Font(bold=True)
    meta["A2"] = source_filename or ""
    meta["A3"] = "Generated"
    meta["A3"].font = Font(bold=True)
    meta["A4"] = date.today().isoformat()
    meta.column_dimensions["A"].width = 40

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer


# --- internals -----------------------------------------------------


def _row_view(finding: dict) -> dict[str, str]:
    """Normalise one finding dict to the canonical row shape produced
    by :mod:`app.utility.finding_projections`. Non-dict inputs collapse
    to all-empty values rather than raising, so a malformed row from a
    runaway validator does not kill the download."""
    if not isinstance(finding, dict):
        return {field: "" for field in _FIELDS}
    return {
        "rule_id": finding.get("rule_id") or "",
        "severity": finding.get("severity") or "",
        "section": finding.get("section") or "",
        "element": finding.get("element") or "",
        "message": finding.get("message") or "",
    }


def _stringify(value) -> str:
    """Coerce None / non-str values to a plain string so formatters
    don't have to branch."""
    if value is None:
        return ""
    return str(value)


def _md_cell(value) -> str:
    """Escape pipes and newlines for a markdown table cell."""
    return _stringify(value).replace("|", "\\|").replace("\n", " ")
