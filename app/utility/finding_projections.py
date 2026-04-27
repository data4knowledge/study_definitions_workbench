"""Projections from the three SDW validation engines into a single
row shape for the shared results template.

The workbench currently calls three independent validators:

* ``usdm4_protocol.validation.m11.M11Validator`` — an M11 DOCX against
  the ICH M11 specification.  Returns
  :class:`usdm4_protocol.validation.common.Results`.
* ``usdm4.USDM4.validate`` — a USDM v4 JSON against the usdm4 Python
  rule library.  Returns
  :class:`usdm4.rules.results.RulesValidationResults`.
* ``usdm4.USDM4.validate_core`` — a USDM v4 JSON against the CDISC
  CORE JSONata rule engine.  Returns
  :class:`usdm4.core.core_validation_result.CoreValidationResult`.

Each engine has its own flat or nested result shape (the docstring on
the source class is the authoritative description).  The workbench's
results page wants a single uniform row so the Jinja template does not
have to know which engine produced the row.  These projections take an
engine result object and return a list of projected rows with the
following keys:

    rule_id    — stable rule identifier
    severity   — ``"error" | "warning" | "info"`` (normalised for the UI)
    section    — where in the document the finding applies
                 (M11 section number / USDM class name /
                  CORE section number + title)
    element    — the specific element or attribute
                 (M11 element name / USDM attribute /
                  CORE entity + instance id)
    message    — human-readable finding text
    rule_text  — optional rule description (may be empty)
    path       — JSON/DOCX path for drill-down (may be empty)

These are **not** a generic abstraction.  They are a thin adapter used
by the router — if the engines evolve or the UI needs different fields
the router changes here and in the template together.  The projections
intentionally live next to the validator call sites rather than inside
a generic utility package.

Defensive behaviour: each projection tolerates a ``None`` input or an
object without the expected ``to_dict``/``findings`` API by returning
``[]``.  This keeps the router robust against unit-test mocks and
against early bail-outs from the extract stage.
"""

from __future__ import annotations

from typing import Any


# ``simple_error_log`` level display names → UI severity bucket.  The
# three-bucket collapse (Error / Warning / Info) is the vocabulary the
# results table and its severity pills speak.  ``Debug`` is folded into
# ``info`` so the UI never surfaces a fourth colour.
_LEVEL_NAME_TO_SEVERITY = {
    "error": "error",
    "warning": "warning",
    "info": "info",
    "debug": "info",
}

# ``simple_error_log`` numeric levels — mirrored here so we don't pull
# in the whole package for constants that are essentially frozen.
_LEVEL_ERROR = 40
_LEVEL_WARNING = 30


def _level_to_severity(level: Any) -> str:
    """Map a ``level`` value (string display name or numeric) to the
    three-value UI severity bucket.  Unknown / missing / garbage
    levels fall back to ``info`` so the UI always has a colour to
    render."""
    if isinstance(level, str):
        return _LEVEL_NAME_TO_SEVERITY.get(level.strip().lower(), "info")
    try:
        numeric = int(level)
    except (TypeError, ValueError):
        return "info"
    if numeric >= _LEVEL_ERROR:
        return "error"
    if numeric >= _LEVEL_WARNING:
        return "warning"
    return "info"


def _rows_from(result: Any) -> list[dict]:
    """Safely call ``result.to_dict()`` and return a list of rows.

    Returns ``[]`` when the input is ``None``, lacks ``to_dict``, or
    ``to_dict`` returns anything other than a list (e.g. test mocks
    that return a dict).  Defensiveness matters because the router
    hits this path on malformed uploads and mocks in unit tests.
    """
    if result is None:
        return []
    rows = result.to_dict() if hasattr(result, "to_dict") else []
    return rows if isinstance(rows, list) else []


def project_m11_result(result: Any) -> list[dict]:
    """Project an M11 ``Results`` object into the shared UI row shape.

    The M11 row already carries ``section`` and ``element`` location
    keys, so the projection is mostly a severity normalisation plus
    field pass-through.  Success / NotImplemented rows have already
    been filtered out by ``Results.to_dict`` — we do not re-filter.
    """
    rows = _rows_from(result)
    return [
        {
            "rule_id": (row.get("rule_id") or "").strip(),
            "severity": _level_to_severity(row.get("level")),
            "section": (row.get("section") or "").strip(),
            "element": (row.get("element") or "").strip(),
            "message": row.get("message") or "",
            "rule_text": row.get("rule_text") or "",
            "path": row.get("path") or "",
        }
        for row in rows
    ]


def project_usdm_rules_result(result: Any) -> list[dict]:
    """Project a ``RulesValidationResults`` object into the shared UI
    row shape.

    USDM JSON has no ``section`` concept — the nearest equivalent is
    the class name plus attribute.  We present ``klass`` as *Section*
    and ``attribute`` as *Element* so the author-audience column names
    stay consistent across engines.  The ``path`` field still carries
    the raw JSONPath for drill-down.
    """
    rows = _rows_from(result)
    return [
        {
            "rule_id": (row.get("rule_id") or "").strip(),
            "severity": _level_to_severity(row.get("level")),
            "section": (row.get("klass") or "").strip(),
            "element": (row.get("attribute") or "").strip(),
            "message": row.get("message") or "",
            "rule_text": row.get("rule_text") or "",
            "path": row.get("path") or "",
        }
        for row in rows
    ]


def project_usdm_core_result(result: Any) -> list[dict]:
    """Project a ``CoreValidationResult`` into the shared UI row shape.

    CORE results are not flat: the top-level carries a list of
    ``CoreRuleFinding`` objects, each with its own list of per-instance
    ``errors`` dicts.  We flatten to one row per (finding, error) pair.

    Section / element are reconstructed from the ``_format_error``
    output that CORE already ships: ``sectionNumber`` + ``sectionTitle``
    form the section label, and ``entity`` + ``instance_id`` together
    identify the element.  Severity is always ``"error"`` because CORE
    does not emit a warning/info vocabulary — everything it surfaces is
    a real-data conformance failure.
    """
    if result is None or not hasattr(result, "findings"):
        return []

    projected: list[dict] = []
    for finding in result.findings or []:
        rule_id = (getattr(finding, "rule_id", "") or "").strip()
        description = getattr(finding, "description", "") or ""
        base_message = getattr(finding, "message", "") or ""
        raw_errors = getattr(finding, "errors", []) or []
        if not raw_errors:
            # Finding reported without per-instance errors — surface
            # the finding itself as one row.  Rare in practice but we
            # must not silently drop it.
            projected.append(
                {
                    "rule_id": rule_id,
                    "severity": "error",
                    "section": "",
                    "element": "",
                    "message": base_message,
                    "rule_text": description,
                    "path": "",
                }
            )
            continue
        for error in raw_errors:
            formatted = _format_core_error(error)
            projected.append(
                {
                    "rule_id": rule_id,
                    "severity": "error",
                    "section": _core_section(formatted),
                    "element": _core_element(formatted),
                    "message": _core_message(base_message, formatted),
                    "rule_text": description,
                    "path": formatted.get("path", "") or "",
                }
            )
    return projected


def project_usdm_rules_summary(result: Any) -> dict:
    """Project the run-level summary fields of a
    ``RulesValidationResults`` (the d4k engine) into a flat dict for
    the results-page header card.

    Parallels :func:`project_usdm_core_summary`.  The d4k engine
    doesn't carry the CT-package or USDM-version context CORE has,
    but it does expose a per-status outcome breakdown
    (Success / Failure / Exception / Not Implemented) that's useful
    enough to surface in the header — especially the *Exception*
    count, which is the d4k-specific signal that a rule blew up
    rather than producing a finding.

    Returns ``{}`` for ``None`` / non-rules inputs so the template can
    use a single ``{% if summary %}`` guard regardless of engine.
    """
    if result is None:
        return {}
    # Duck-type — ``outcomes`` and ``count`` are stable across the
    # engine's public API and uniquely identify a
    # ``RulesValidationResults``.  Match against ``count`` so we don't
    # accidentally classify a CORE result (which has neither) here.
    if not hasattr(result, "outcomes") or not callable(getattr(result, "count", None)):
        return {}

    outcomes = getattr(result, "outcomes", {}) or {}
    by_status: dict[str, int] = {
        "Success": 0,
        "Failure": 0,
        "Exception": 0,
        "Not Implemented": 0,
    }
    rules_with_findings = 0
    for outcome in outcomes.values():
        # ``status`` is a ``RuleStatus`` enum but the value is a string
        # ("Success" / "Failure" / …).  ``str(status)`` would give us
        # ``RuleStatus.SUCCESS`` so reach for ``.value`` and fall back
        # to ``str()`` for mocks that pass plain strings.
        status_value = getattr(getattr(outcome, "status", None), "value", None)
        if status_value is None:
            status_value = str(getattr(outcome, "status", "") or "")
        if status_value in by_status:
            by_status[status_value] += 1
        if status_value == "Failure" and getattr(outcome, "error_count", 0):
            rules_with_findings += 1

    finding_count = int(getattr(result, "finding_count", 0) or 0)
    return {
        # Discriminator for the results-page header card. The user-
        # facing label everywhere else in the workbench (validate
        # menu, results card title, download filenames) is "d4k", so
        # we use that here too rather than the internal "rules"
        # naming used by the projector function name.
        "engine": "d4k",
        # ``RulesValidationResults`` doesn't carry a USDM version on
        # the result object — the version belongs to the input file,
        # not the engine.  We leave this empty so the header subtitle
        # collapses cleanly.
        "version": "",
        "file_path": "",
        "rules_executed": int(result.count()),
        "rules_skipped": 0,  # d4k engine doesn't surface a skipped count
        "finding_count": finding_count,
        "rule_count": rules_with_findings,
        "success_count": by_status["Success"],
        "failure_count": by_status["Failure"],
        "exception_count": by_status["Exception"],
        "not_implemented_count": by_status["Not Implemented"],
    }


def project_usdm_core_summary(result: Any) -> dict:
    """Project the run-level summary fields of a ``CoreValidationResult``
    into a flat dict for the results-page header card.

    The CORE engine returns a substantial run-level context that the
    findings table alone cannot show — how many rules ran, how many
    errored out before they could check anything, which CT packages
    were loaded, etc.  See
    :class:`usdm4.core.core_validation_result.CoreValidationResult`
    for the authoritative shape.

    Returns ``{}`` for non-CORE / ``None`` / unexpected inputs so the
    template can use a single ``{% if summary %}`` guard.  The dict is
    flat (not nested) so the template doesn't need helper macros to
    pull values out.
    """
    if result is None:
        return {}
    # Duck-type — the CORE summary fields are unique enough that
    # presence of ``rules_executed`` is a sufficient signal.  This
    # keeps the projection robust against mocks that don't import the
    # real dataclass.
    if not hasattr(result, "rules_executed"):
        return {}
    ct_loaded = list(getattr(result, "ct_packages_loaded", []) or [])
    findings = getattr(result, "findings", []) or []
    finding_count = sum(
        len(getattr(f, "errors", []) or []) for f in findings
    )
    execution_errors = list(getattr(result, "execution_errors", []) or [])
    return {
        "engine": "core",
        "version": getattr(result, "version", "") or "",
        "file_path": getattr(result, "file_path", "") or "",
        "rules_executed": int(getattr(result, "rules_executed", 0) or 0),
        "rules_skipped": int(getattr(result, "rules_skipped", 0) or 0),
        "finding_count": finding_count,
        "rule_count": len(findings),
        "execution_error_count": len(execution_errors),
        "ct_packages_available": int(
            getattr(result, "ct_packages_available", 0) or 0
        ),
        "ct_packages_loaded": ct_loaded,
        "ct_packages_loaded_count": len(ct_loaded),
    }


# ---- CORE helpers -----------------------------------------------------


def _format_core_error(error: Any) -> dict[str, Any]:
    """Flatten a raw CORE engine error dict to the flat shape the
    projection consumes.

    The CORE engine hands us each error as a nested dict — the
    identity fields are at the top level, while section and domain
    fields live inside a ``value`` sub-dict.  This helper pulls the
    fields we care about up to the top level:

        * ``instance_id``, ``entity``, ``path`` — copied straight
          across if present.
        * ``name`` / ``sectionNumber`` / ``sectionTitle`` — copied
          from ``value``.
        * other non-identity ``value`` keys — rolled into a
          ``details`` dict so :func:`_core_message` can concatenate
          them into a readable per-error tail.

    Non-dict inputs are wrapped in a minimal ``{"detail": ...}`` dict
    so downstream code can still subscript safely.  Never raises.

    The helper is intentionally self-contained rather than calling
    ``CoreRuleFinding._format_error`` — that method is private to
    ``usdm4`` and has a slightly different contract (it also strips
    ``*.id`` / ``*.name`` / ``*.version`` keys from details and
    sanitises jsonata types).  We don't need those features for the
    UI row, and inlining keeps the projection module self-contained.
    """
    if not isinstance(error, dict):
        return {"detail": str(error) if error is not None else ""}

    formatted: dict[str, Any] = {}
    for key in ("instance_id", "entity", "path"):
        if key in error:
            formatted[key] = error[key]

    value = error.get("value")
    if isinstance(value, dict):
        for key in ("name", "sectionNumber", "sectionTitle"):
            if key in value:
                formatted[key] = value[key]
        skip = {"instanceType", "id", "path", "name", "sectionNumber", "sectionTitle"}
        extras = {k: v for k, v in value.items() if k not in skip}
        if extras:
            formatted["details"] = extras
    elif value is not None:
        formatted["value"] = value

    for key in ("error", "message", "detail"):
        if error.get(key):
            formatted[key] = error[key]

    return formatted


def _core_section(formatted: dict) -> str:
    number = str(formatted.get("sectionNumber", "") or "").strip()
    title = str(formatted.get("sectionTitle", "") or "").strip()
    if number and title:
        return f"{number} {title}"
    return number or title


def _core_element(formatted: dict) -> str:
    entity = str(formatted.get("entity", "") or "").strip()
    instance_id = str(formatted.get("instance_id", "") or "").strip()
    name = str(formatted.get("name", "") or "").strip()
    if entity and instance_id:
        return f"{entity} ({instance_id})"
    return entity or name or instance_id


def _core_message(base: str, formatted: dict) -> str:
    """Compose a human-readable message for a CORE error row.

    ``CoreRuleFinding.message`` is the rule-level message shared by
    every error under that finding; per-error detail lives in
    ``formatted["details"]`` (a dict of field → value pairs) or in a
    ``detail`` / ``error`` / ``message`` key for non-structured errors.
    We concatenate rule-level and per-error text so the row is
    self-contained in a flat table.
    """
    extras: list[str] = []
    details = formatted.get("details")
    if isinstance(details, dict) and details:
        extras.append(", ".join(f"{k}={v}" for k, v in details.items()))
    for key in ("detail", "error", "message"):
        value = formatted.get(key)
        if value and value != base:
            extras.append(str(value))
    if not extras:
        return base
    suffix = "; ".join(extras)
    return f"{base} ({suffix})" if base else suffix
