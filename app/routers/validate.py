import json
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import user_details
from app.dependencies.templates import templates
from app.configuration.configuration import application_configuration
from app.model.file_handling.local_files import LocalFiles
from app.model.file_handling.data_files import DataFiles
from usdm_info import __model_version__ as usdm_version
from app.database.user import User

from app.imports.form_handler import FormHandler
from app.utility.findings_export import (
    default_filename,
    sanitise_filename,
    to_csv as findings_to_csv,
    to_json as findings_to_json,
    to_markdown as findings_to_markdown,
    to_xlsx as findings_to_xlsx,
)
from usdm4 import USDM4, RulesValidationResults
from usdm3 import USDM3
from usdm4_protocol.validation.m11 import M11Validator
from simple_error_log import Errors as M11Errors
from app.utility.finding_projections import (
    project_m11_result,
    project_m11_summary,
    project_usdm_cdisc_result,
    project_usdm_cdisc_summary,
    project_usdm_d4k_result,
    project_usdm_d4k_summary,
)

router = APIRouter(
    prefix="/validate", tags=["validate"], dependencies=[Depends(protect_endpoint)]
)


@router.get("/usdm3", dependencies=[Depends(protect_endpoint)])
def validate_usdm3(request: Request, session: Session = Depends(get_db)):
    return _validate_setup(
        request,
        session,
        "json",
        False,
        "/validate/usdm3",
        "validate/partials/validate_json.html",
        {"version": "3.0.0"},
    )


@router.get("/usdm", dependencies=[Depends(protect_endpoint)])
def validate_usdm(request: Request, session: Session = Depends(get_db)):
    """Default USDM v4 picker. Routes through the CDISC engine — CDISC
    is the workbench's default validator, with d4k available as the
    sibling ``/validate/usdm/d4k`` route. The validate dropdown in
    ``shared/partials/validate_menu.html`` skips this default in
    favour of explicit engine routes, so this entry point is reached
    only via direct URL / bookmarks."""
    return _validate_setup(
        request,
        session,
        "json",
        False,
        "/validate/usdm",
        "validate/partials/validate_json.html",
        {"version": usdm_version, "engine": "CDISC"},
    )


@router.post("/usdm3", dependencies=[Depends(protect_endpoint)])
async def validate_usdm3_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await _process(request, user, USDM3(), source)


@router.post("/usdm", dependencies=[Depends(protect_endpoint)])
async def validate_usdm_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    """POST companion to the default ``/validate/usdm`` picker. Defers
    to the shared ``_process_usdm_engine`` helper with the CDISC
    engine — keeps the default route's results page identical to
    ``/validate/usdm/cdisc`` rather than the bare-bones output of
    ``_process``."""
    user, present_in_db = user_details(request, session)
    return await _process_usdm_engine(request, user, source, engine="cdisc")


@router.get("/usdm/d4k", dependencies=[Depends(protect_endpoint)])
def validate_usdm_d4k(request: Request, session: Session = Depends(get_db)):
    """File picker for USDM v4 d4k engine validation (the ``usdm4``
    Python rule library). Reuses the shared USDM JSON picker — only the
    data URL and the engine label differ from ``/validate/usdm/cdisc``."""
    return _validate_setup(
        request,
        session,
        "json",
        False,
        "/validate/usdm/d4k",
        "validate/partials/validate_json.html",
        {"version": usdm_version, "engine": "d4k"},
    )


@router.post("/usdm/d4k", dependencies=[Depends(protect_endpoint)])
async def validate_usdm_d4k_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await _process_usdm_engine(request, user, source, engine="d4k")


@router.get("/usdm/cdisc", dependencies=[Depends(protect_endpoint)])
def validate_usdm_cdisc(request: Request, session: Session = Depends(get_db)):
    """File picker for USDM v4 CDISC engine validation (CORE — the only
    CDISC engine, so the route just says CDISC). CORE runs can take
    several minutes on a cold cache — surfaced via the displayed engine
    label on the picker page. See ``usdm4.USDM4.validate_core`` for
    cache_dir / api_key wiring."""
    return _validate_setup(
        request,
        session,
        "json",
        False,
        "/validate/usdm/cdisc",
        "validate/partials/validate_json.html",
        {"version": usdm_version, "engine": "CDISC"},
    )


@router.post("/usdm/cdisc", dependencies=[Depends(protect_endpoint)])
async def validate_usdm_cdisc_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await _process_usdm_engine(request, user, source, engine="cdisc")


@router.get("/m11-docx", dependencies=[Depends(protect_endpoint)])
def validate_m11_docx(request: Request, session: Session = Depends(get_db)):
    """File picker for M11 ``.docx`` validation. The DOCX is run through
    the standalone :class:`M11Validator` — no USDM4 translation step."""
    return _validate_setup(
        request,
        session,
        "docx",
        False,
        "/validate/m11-docx",
        "validate/partials/validate_m11_docx.html",
        {"version": "ICH M11 (2025-11-16)"},
    )


@router.post("/m11-docx", dependencies=[Depends(protect_endpoint)])
async def validate_m11_docx_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await _process_m11_docx(request, user, source)


@staticmethod
def _validate_setup(
    request: Request,
    session: Session,
    ext: str,
    other_file: bool,
    data_url: str,
    page_html: str,
    extra_data: dict = {},
):
    user, present_in_db = user_details(request, session)
    data = application_configuration.file_picker
    data.update(extra_data)
    data["dir"] = LocalFiles().root if data["os"] else ""
    data["required_ext"] = ext
    data["other_files"] = other_file
    data["url"] = data_url
    return templates.TemplateResponse(request, page_html, {"user": user, "data": data})


def _strip_accepted_messages(messages: list[str]) -> list[str]:
    """Drop ``FormHandler``'s informational "File 'X' accepted" /
    "Image file 'X' accepted" banner from the messages list before it
    reaches the results template.

    The banner makes sense on background imports (where the user wants
    a "we got your file" signal while the import runs asynchronously),
    but is just noise on the foreground validation flows — the user is
    already watching the findings table appear, so confirming the
    upload landed is redundant. Operational warnings ("File 'X' was
    ignored ...", "Failed to process the validation file") remain.
    """
    return [m for m in messages if not m.endswith(" accepted")]


@staticmethod
async def _process(request: Request, user: User, usdm: USDM3 | USDM4, source: str):
    form_handler = FormHandler(
        request,
        False,
        ".json",
        source,
    )
    main_file, image_files, messages = await form_handler.get_files()
    findings: list[dict] = []
    if main_file:
        files = DataFiles()
        _ = files.new()
        files.save("usdm", main_file["contents"], main_file["filename"])
        full_path, filename, exists = files.path("usdm")
        results: RulesValidationResults = usdm.validate(full_path)
        # Project the engine's row shape into the shared UI row shape
        # consumed by ``validate/partials/results.html``.  See
        # ``app/utility/finding_projections.py`` for the row contract.
        findings = project_usdm_d4k_result(results)
        files.delete()
    else:
        print(f"Messages: {messages}")
        messages.append("Failed to process the validation file")
    return templates.TemplateResponse(
        request,
        "validate/partials/results.html",
        {
            "user": user,
            "data": {
                "filename": main_file,
                "messages": _strip_accepted_messages(messages),
                "findings": findings,
            },
        },
    )


@staticmethod
async def _process_usdm_engine(request: Request, user: User, source: str, engine: str):
    """Shared handler for the two USDM v4 validation flows.

    ``engine`` is ``"d4k"`` (the d4k / usdm4 Python rule library,
    :meth:`USDM4.validate`) or ``"cdisc"`` (CDISC CORE JSONata engine,
    :meth:`USDM4.validate_core` — CORE is the only CDISC engine, so the
    workbench labels it just ``cdisc``). Both return engine-native
    result objects that we project into the shared UI row shape via
    :mod:`app.utility.finding_projections` before rendering the common
    ``validate/partials/results.html`` template. The header card uses
    the same ``"d4k"`` / ``"cdisc"`` discriminator on
    ``summary['engine']`` to pick its title and per-engine subtitle
    extras, so the dispatch hint and the template tag stay in sync.

    The CORE run can take several minutes on a cold cache — today this
    call is synchronous which means the HTMX swap blocks until the
    engine returns. Background execution is tracked as an SDW roadmap
    item (see ``docs/next_steps.md``); wiring it in changes the route
    shape, not this helper.
    """
    form_handler = FormHandler(request, False, ".json", source)
    main_file, image_files, messages = await form_handler.get_files()
    findings: list[dict] = []
    summary: dict = {}
    if main_file:
        files = DataFiles()
        _ = files.new()
        files.save("usdm", main_file["contents"], main_file["filename"])
        full_path, filename, exists = files.path("usdm")
        # Pass the configured CORE cache path (empty string falls through
        # to the USDM4 platform default). This keeps the downloaded
        # JSONata files, XSD schemas, rules, and CT packages on the
        # mounted volume so they survive container restarts — a cold
        # cache run can take several minutes.
        usdm = USDM4(cache_dir=application_configuration.cdisc_core_cache_path or None)
        if engine == "cdisc":
            results = usdm.validate_core(full_path)
            findings = project_usdm_cdisc_result(results)
            # CDISC's CORE engine returns a rich run-level context
            # (rules executed / skipped, execution errors, CT packages
            # loaded, …) that the d4k engine has no equivalent for.
            # Surface it via the results-page header card.
            # ``project_usdm_cdisc_summary`` returns ``{}`` for non-CDISC
            # / None inputs so the template can use a single
            # ``{% if summary %}`` guard.
            summary = project_usdm_cdisc_summary(results)
            download_kind = "usdm-cdisc-findings"
            download_title = "USDM v4 CDISC Findings"
            download_sheet = "USDM CDISC Findings"
        else:
            # ``d4k`` is the default — ``engine`` values other than
            # ``"cdisc"`` fall through here so a typo doesn't silently
            # swap engines.
            results = usdm.validate(full_path)
            findings = project_usdm_d4k_result(results)
            # Mirror the CDISC flow: feed the run-level outcome
            # breakdown (rules executed / failures / exceptions / not-
            # implemented) into the header card so the d4k results
            # page reads as a sibling of the CDISC one.
            summary = project_usdm_d4k_summary(results)
            # Stamp the validated USDM version onto the summary —
            # ``RulesValidationResults`` doesn't carry one of its own
            # (the version belongs to the file, not the engine), and
            # for the d4k engine the workbench currently only ships
            # validation against the active ``usdm_version``.
            summary["version"] = usdm_version
            download_kind = "usdm-d4k-findings"
            download_title = "USDM v4 d4k Findings"
            download_sheet = "USDM d4k Findings"
        files.delete()
    else:
        messages.append("Failed to process the validation file")
        download_kind = (
            "usdm-cdisc-findings" if engine == "cdisc" else "usdm-d4k-findings"
        )
        download_title = (
            "USDM v4 CDISC Findings" if engine == "cdisc" else "USDM v4 d4k Findings"
        )
        download_sheet = (
            "USDM CDISC Findings" if engine == "cdisc" else "USDM d4k Findings"
        )
    # HTMX retarget: the picker (``import/partials/browser_file_select.html``)
    # wraps its form in an outer ``#picker_card`` with title /
    # subtitle.  Once results are rendered the result page already
    # carries that identity in its own header card, so we tell HTMX to
    # replace the *whole* picker card (``HX-Retarget: #picker_card``,
    # ``HX-Reswap: outerHTML``) rather than swapping into the form
    # ``#form_div`` inside it.  Result: the file-picker chrome
    # disappears in one swap — no OOB fragments, no order-of-operations
    # surprises — and we reuse the picker page's outer column layout.
    return templates.TemplateResponse(
        request,
        "validate/partials/results.html",
        {
            "user": user,
            "data": {
                "filename": main_file,
                "messages": _strip_accepted_messages(messages),
                "findings": findings,
                "summary": summary,
                "download_kind": download_kind,
                "download_title": download_title,
                "download_sheet": download_sheet,
            },
        },
        headers={
            "HX-Retarget": "#picker_card",
            "HX-Reswap": "outerHTML",
        },
    )


@staticmethod
async def _process_m11_docx(request: Request, user: User, source: str):
    """Process an uploaded M11 ``.docx`` through the standalone M11
    validator and render the unified findings template.

    Mirrors ``_process_usdm_engine`` for USDM JSON. Differences:
    ``.docx`` extension and the :class:`M11Validator` entry point
    (DOCX-layer, no translator). Renders the same
    ``validate/partials/results.html`` partial as the CDISC and d4k
    flows so the three validation result pages share one layout — the
    template branches on ``summary['engine']`` to pick the M11 title
    and skip USDM-only header extras.

    The annotated-protocol view has been removed from this standalone
    flow (task #36). It will be rehomed under the study view's
    validation panel in task #40, where a rendered protocol already
    exists to hang markers on.
    """
    form_handler = FormHandler(
        request,
        False,
        ".docx",
        source,
    )
    main_file, image_files, messages = await form_handler.get_files()
    findings: list[dict] = []
    summary: dict = {}
    if main_file:
        files = DataFiles()
        _ = files.new()
        # Reuse the existing "docx" media type; "m11" isn't registered in
        # DataFiles.media_type and shouldn't be added just for validation.
        files.save("docx", main_file["contents"], main_file["filename"])
        full_path, filename, exists = files.path("docx")
        # Standalone validator — runs against the DOCX directly without
        # going through the USDM4 translator.  See
        # usdm4_protocol/docs/m11_validator_v2_plan.md for the design.
        validator_errors = M11Errors()
        results = M11Validator(full_path, validator_errors).validate()
        # Project the M11 engine's Results object into the shared UI row
        # shape and summary dict consumed by
        # ``validate/partials/results.html``.
        findings = project_m11_result(results)
        summary = project_m11_summary(results, findings)
        if results.count() == 0 and validator_errors.count() > 0:
            # Reader or runner failed before any rule could run —
            # surface the operational problem rather than claim
            # success.
            messages.append("Validation could not be completed (extraction failed).")
        files.delete()
    else:
        messages.append("Failed to process the validation file")
    # HTMX retarget mirrors the USDM v4 flows: replace the whole
    # ``#picker_card`` with the rendered results card in one swap so
    # the picker chrome (title / subtitle / border) disappears
    # cleanly.  The unified template carries its own header card with
    # the M11 identity, so no out-of-band fragments are needed.
    return templates.TemplateResponse(
        request,
        "validate/partials/results.html",
        {
            "user": user,
            "data": {
                "filename": main_file,
                "messages": _strip_accepted_messages(messages),
                "findings": findings,
                "summary": summary,
                # Download metadata shared with the USDM v4 flows — the
                # results template passes these through to the
                # hidden-input form so /validate/download/{csv,json,md,
                # xlsx} produces filenames and headings tagged for M11.
                "download_kind": "m11-findings",
                "download_title": "M11 Validation Findings",
                "download_sheet": "M11 Findings",
            },
        },
        headers={
            "HX-Retarget": "#picker_card",
            "HX-Reswap": "outerHTML",
        },
    )


# --- Findings download routes ------------------------------------
#
# The results page has a plain HTML form with four submit buttons, each
# targeting one of the routes below. Form fields:
#   * ``findings`` — the findings JSON (hidden input rendered by the
#     results template);
#   * ``source_filename`` — the uploaded file name, used to build a
#     deterministic download filename like
#     ``WP45338-m11-findings-2026-04-19.csv``;
#   * ``kind`` — validator tag that slots into the filename
#     (``m11-findings`` / ``usdm-d4k-findings`` /
#     ``usdm-cdisc-findings``). Defaults to ``m11-findings`` because
#     M11 was the first caller; new callers should set it explicitly.
#   * ``title`` — heading used on the Markdown export.
#   * ``sheet_title`` — worksheet name on the XLSX export.
#
# The routes share a small helper (``_download_response``) so each
# format-specific handler is a two-line method call. Keeping one route
# per format rather than dispatching by a ``format`` query parameter
# avoids clients having to escape / URL-build, and lets each route
# have a clear, CURL-friendly URL.
#
# Routes are mounted under ``/validate/download/{fmt}`` (not
# ``/validate/m11-docx/download/...``) so the USDM v4 CDISC and USDM v4
# d4k validation flows can share them.


def _parse_findings(findings_json: str) -> list[dict]:
    """Parse the hidden-input findings JSON. Returns ``[]`` on empty /
    malformed input rather than raising — the downstream formatters
    all tolerate an empty list cleanly."""
    if not findings_json:
        return []
    try:
        parsed = json.loads(findings_json)
    except (json.JSONDecodeError, TypeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _download_response(
    body: bytes,
    filename: str,
    media_type: str,
) -> Response:
    """Wrap a serialised payload in an HTTP response that triggers a
    download, with a safely-sanitised filename on the
    Content-Disposition header."""
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/download/csv", dependencies=[Depends(protect_endpoint)])
async def validate_download_csv(
    findings: str = Form(""),
    source_filename: str = Form("protocol.docx"),
    kind: str = Form("m11-findings"),
):
    default = default_filename(source_filename, "csv", kind=kind)
    filename = sanitise_filename(default, default)
    return _download_response(
        findings_to_csv(_parse_findings(findings)),
        filename,
        "text/csv; charset=utf-8",
    )


@router.post("/download/json", dependencies=[Depends(protect_endpoint)])
async def validate_download_json(
    findings: str = Form(""),
    source_filename: str = Form("protocol.docx"),
    kind: str = Form("m11-findings"),
):
    default = default_filename(source_filename, "json", kind=kind)
    filename = sanitise_filename(default, default)
    return _download_response(
        findings_to_json(_parse_findings(findings)),
        filename,
        "application/json; charset=utf-8",
    )


@router.post("/download/md", dependencies=[Depends(protect_endpoint)])
async def validate_download_md(
    findings: str = Form(""),
    source_filename: str = Form("protocol.docx"),
    kind: str = Form("m11-findings"),
    title: str = Form("M11 Validation Findings"),
):
    default = default_filename(source_filename, "md", kind=kind)
    filename = sanitise_filename(default, default)
    return _download_response(
        findings_to_markdown(_parse_findings(findings), source_filename, title=title),
        filename,
        "text/markdown; charset=utf-8",
    )


@router.post("/download/xlsx", dependencies=[Depends(protect_endpoint)])
async def validate_download_xlsx(
    findings: str = Form(""),
    source_filename: str = Form("protocol.docx"),
    kind: str = Form("m11-findings"),
    sheet_title: str = Form("M11 Findings"),
):
    default = default_filename(source_filename, "xlsx", kind=kind)
    filename = sanitise_filename(default, default)
    buffer = findings_to_xlsx(
        _parse_findings(findings), source_filename, sheet_title=sheet_title
    )
    return StreamingResponse(
        buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
