import json
import yaml
from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from d4k_ms_ui.pagination import Pagination
from d4k_ms_base.logger import application_logger
from app.database.user import User
from app.database.version import Version
from app.database.database import get_db
from app.database.file_import import FileImport
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import transmit_role_enabled, user_details
from app.dependencies.templates import templates
from app.model.usdm_json import USDMJson
from app.dependencies.fhir_version import fhir_versions
from app.usdm_database.usdm_database import USDMDatabase
from app.configuration.configuration import application_configuration
from app.model.file_handling.local_files import LocalFiles
from app.model.file_handling.data_files import DataFiles
from app.imports.form_handler import FormHandler
from app.utility.m11_annotate import annotate as m11_annotate
from usdm4_protocol.m11 import USDM4M11
from usdm4_protocol.cpt import USDM4CPT
from usdm4.api import Wrapper


router = APIRouter(
    prefix="/versions", tags=["versions"], dependencies=[Depends(protect_endpoint)]
)


@router.get("/{id}/summary")
async def get_version_summary(
    request: Request, id: int, session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(id, session)
    data = {
        "version": usdm.study_version(),
        "templates": usdm.templates(),
        "endpoints": User.endpoints_page(1, 100, user.id, session),
        "fhir": {
            "enabled": transmit_role_enabled(request),
            "versions": fhir_versions(),
        },
        "m11": getattr(usdm, "m11", False),
    }
    # print(f"DATA: {data}")
    return templates.TemplateResponse(
        request, "study_versions/summary.html", {"user": user, "data": data}
    )


@router.get("/{id}/load/{load_type}", dependencies=[Depends(protect_endpoint)])
def import_yaml(
    request: Request, id: str, load_type: str, session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    data = application_configuration.file_picker
    data["dir"] = LocalFiles().root if data["os"] else ""
    data["required_ext"] = "yaml"
    data["other_files"] = False
    data["url"] = f"/versions/{id}/load/{load_type}"
    data["load_type"] = load_type
    return templates.TemplateResponse(
        request, "study_versions/load.html", {"user": user, "data": data}
    )


@router.post("/{id}/load/{load_type}", dependencies=[Depends(protect_endpoint)])
async def import_yaml_process(
    request: Request,
    id: str,
    load_type: str,
    source: str = "browser",
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(id, session)
    form_handler = FormHandler(
        request,
        False,
        "yaml",
        source,
    )
    main_file, _, messages = await form_handler.get_files()
    df = DataFiles(usdm.uuid)
    filename = main_file["filename"]
    contents = yaml.safe_load(main_file["contents"].decode())
    full_path, _ = df.save(load_type, contents, filename)
    if full_path:
        return templates.TemplateResponse(
            request,
            "import/partials/upload_success.html",
            {
                "filename": main_file["filename"],
                "messages": messages,
                "route": f"/versions/{id}/summary",
                "label": "Back to study",
            },
        )
    else:
        messages.append("Failed to save the load file")
        return templates.TemplateResponse(
            request,
            "import/partials/upload_fail.html",
            {
                "filename": main_file["filename"],
                "messages": messages,
                "type": load_type,
            },
        )


@router.get("/{id}/history")
async def get_version_history(
    request: Request, id: int, session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(id, session)
    data = {
        "version": usdm.study_version(),
        "version_id": id,
        "page": 1,
        "size": 10,
        "filter": "",
        "m11": getattr(usdm, "m11", False),
    }
    return templates.TemplateResponse(
        request, "study_versions/history.html", {"user": user, "data": data}
    )


@router.get("/{id}/validation")
async def get_version_validation(
    request: Request, id: int, session: Session = Depends(get_db)
):
    """Render the Validation panel for an M11-origin study.

    Reads the persisted ``m11_validation`` JSON (written during the
    M11 import via :class:`ImportM11` in ``app/imports/import_processors.py``).
    Pairs those findings with a freshly rendered M11 HTML view of the
    imported USDM and overlays anchored markers via
    :func:`app.utility.m11_annotate.annotate`. The DOCX itself is *not*
    re-validated here — the findings were captured at import time so
    this view is deterministic and cheap to re-render.

    Non-M11 studies, or M11 studies without a persisted findings file,
    render the same template with ``available=False`` so the user sees
    an explanatory empty state rather than a 404.
    """
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(id, session)
    is_m11 = getattr(usdm, "m11", False)
    df = DataFiles(usdm.uuid)
    findings: list[dict] = []
    annotated_html = ""
    unplaced: list[dict] = []
    placed_count = 0
    available = False
    messages: list[str] = []
    if is_m11:
        full_path, _filename, exists = df.generic_path("m11_validation")
        if exists:
            try:
                with open(full_path, "r") as fh:
                    findings = json.load(fh) or []
                available = True
            except Exception as e:
                application_logger.exception(
                    f"Failed to read m11_validation file '{full_path}'", e
                )
                messages.append("Failed to read the M11 validation findings file.")
    if available:
        try:
            usdm_path, _, _ = usdm.json()
            rendered = USDM4M11().to_html(usdm_path)
            annotated = m11_annotate(rendered, findings)
            annotated_html = annotated.html
            unplaced = annotated.unplaced
            placed_count = annotated.placed_count
        except Exception as e:
            application_logger.exception("Failed to render annotated protocol", e)
            messages.append("Failed to render the annotated protocol view.")
    data = {
        "version": usdm.study_version(),
        "m11": is_m11,
        "available": available,
        "findings": findings,
        "annotated_html": annotated_html,
        "unplaced": unplaced,
        "placed_count": placed_count,
        "messages": messages,
        "filename": None,
        "download_kind": "m11-findings",
        "download_title": "M11 Validation Findings",
        "download_sheet": "M11 Findings",
    }
    return templates.TemplateResponse(
        request, "study_versions/validation.html", {"user": user, "data": data}
    )


@router.get("/{id}/history/data")
async def get_version_history_data(
    request: Request,
    id: int,
    page: int,
    size: int,
    filter: str = "",
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    version = Version.find(id, session)
    data = Version.page(page, size, filter, version.study_id, session)
    for item in data["items"]:
        item["import"] = FileImport.find(item["import_id"], session)
    pagination = Pagination(data, f"/versions/{id}/history/data")
    return templates.TemplateResponse(
        request,
        "study_versions/partials/history.html",
        {"user": user, "pagination": pagination, "data": data},
    )


@router.get("/{id}/export/excel")
async def export_excel(
    request: Request, id: int, version: str = "4", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    usdm_db = USDMDatabase(id, session)
    full_path, filename, media_type = usdm_db.excel(version)
    if full_path:
        return FileResponse(path=full_path, filename=filename, media_type=media_type)
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {
                    "error": f"Error downloading the requested Excel (USDM v{version}) format file"
                },
            },
        )


@router.get("/{id}/protocol")
async def protocol(
    request: Request, id: int, template: str, session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(id, session)
    full_path, _, _ = usdm.json()
    if full_path:
        _, html = _generate_protocol(template, full_path, usdm)
        data = {
            "version": usdm.study_version(),
            "document": html,
            "m11": getattr(usdm, "m11", False),
        }
        return templates.TemplateResponse(
            request, "study_versions/protocol.html", {"user": user, "data": data}
        )
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {"error": "Error locating the USDM JSON file"},
            },
        )


@router.get("/{id}/protocol/export")
async def export_protocol(
    request: Request, id: int, template: str, session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    application_logger.info("PROTOCOL EXPORT")
    usdm = USDMJson(id, session)
    full_path, _, _ = usdm.json()
    file_type, html = _generate_protocol(template, full_path, usdm, export=True)
    protocol_path, filename = usdm._files.save(file_type, html)
    if protocol_path:
        return FileResponse(
            path=protocol_path, filename=filename, media_type="text/html"
        )
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {
                    "error": f"Error downloading the requested protocol ({template}) file"
                },
            },
        )


def _generate_protocol(
    template: str, full_path: str, usdm: USDMJson, export: bool = False
) -> tuple[str, str]:
    html = ""
    file_type = ""
    if template.upper() == "M11":
        if export:
            body = USDM4M11().to_html(full_path)
            t = templates.get_template("study_versions/m11_protocol_export.html")
            html = t.render({"content": body})
        else:
            html = USDM4M11().to_html(full_path)
        file_type = "m11-protocol"
    elif template.upper() == "CPT":
        html = USDM4CPT().to_html(full_path)
        file_type = "cpt-protocol"
    else:
        wrapper: Wrapper = usdm.wrapper()
        html = wrapper.to_html(template)
        file_type = "other-protocol"
    return file_type, html
