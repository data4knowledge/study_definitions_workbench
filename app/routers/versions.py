import yaml
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from d4k_ms_ui.pagination import Pagination
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
        "endpoints": User.endpoints_page(1, 100, user.id, session),
        "fhir": {
            "enabled": transmit_role_enabled(request),
            "versions": fhir_versions(),
        },
    }
    # print(f"DATA: {data}")
    return templates.TemplateResponse(
        request, "study_versions/summary.html", {"user": user, "data": data}
    )


@router.get("/{id}/load/{load_type}", dependencies=[Depends(protect_endpoint)])
def import_xl(
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
        request, f"study_versions/load.html", {"user": user, "data": data}
    )


@router.post("/{id}/load/{load_type}", dependencies=[Depends(protect_endpoint)])
async def import_xl_process(
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
            "import/partials/upload_success.html",
            {
                "request": request,
                "filename": main_file["filename"],
                "messages": messages,
                "route": f"/versions/{id}/summary",
                "label": "Back to study",
            },
        )
    else:
        messages.append("Failed to save the load file")
        return templates.TemplateResponse(
            "import/partials/upload_fail.html",
            {
                "request": request,
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
    }
    return templates.TemplateResponse(
        request, "study_versions/history.html", {"user": user, "data": data}
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
