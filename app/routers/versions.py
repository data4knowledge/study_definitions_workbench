from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from d4kms_ui.pagination import Pagination
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
    return templates.TemplateResponse(
        request, "study_versions/summary.html", {"user": user, "data": data}
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
async def get_version_history(
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
async def export_excel(request: Request, id: int, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    usdm_db = USDMDatabase(id, session)
    full_path, filename, media_type = usdm_db.excel()
    if full_path:
        return FileResponse(path=full_path, filename=filename, media_type=media_type)
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {"error": "Error downloading the requested Excel file"},
            },
        )
