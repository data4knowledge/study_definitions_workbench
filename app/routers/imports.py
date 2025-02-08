from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import user_details
from app.dependencies.templates import templates
from app.configuration.configuration import application_configuration
from app.model.file_handling.local_files import LocalFiles
from app.dependencies.fhir_version import check_fhir_version
from app.model.file_handling.data_files import DataFiles
from d4kms_generic import application_logger
from d4kms_ui.pagination import Pagination
from app.utility.upload import *
from app.database.file_import import FileImport
from usdm_info import __model_version__ as usdm_version

router = APIRouter(
    prefix="/import", tags=["import"], dependencies=[Depends(protect_endpoint)]
)


@router.get("/usdm3", dependencies=[Depends(protect_endpoint)])
def import_usdm3(request: Request, session: Session = Depends(get_db)):
    return _import_setup(
        request,
        session,
        "json",
        False,
        "/import/usdm3",
        "import/import_json.html",
        {"version": "3.0.0"},
    )


@router.get("/usdm4", dependencies=[Depends(protect_endpoint)])
def import_usdm4(request: Request, session: Session = Depends(get_db)):
    return _import_setup(
        request,
        session,
        "json",
        False,
        "/import/usdm4",
        "import/import_json.html",
        {"version": usdm_version},
    )


@router.get("/m11", dependencies=[Depends(protect_endpoint)])
def import_m11(request: Request, session: Session = Depends(get_db)):
    return _import_setup(
        request, session, "docx", False, "/import/m11", "import/import_m11.html"
    )


@router.get("/xl", dependencies=[Depends(protect_endpoint)])
def import_xl(request: Request, session: Session = Depends(get_db)):
    return _import_setup(
        request, session, "xlsx", True, "/import/xl", "import/import_xl.html"
    )


@router.get("/fhir", dependencies=[Depends(protect_endpoint)])
def import_fhir(request: Request, version: str, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    valid, description = check_fhir_version(version)
    if valid:
        return _import_setup(
            request,
            session,
            "json",
            False,
            "/import/fhir",
            "import/import_fhir.html",
            {"version": version, "description": description},
        )
    else:
        message = f"Invalid FHIR version '{version}'"
        application_logger.error(message)
        return templates.TemplateResponse(
            request, "errors/error.html", {"user": user, "data": {"error": message}}
        )


@router.post("/m11", dependencies=[Depends(protect_endpoint)])
async def import_m11(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await process_m11(request, templates, user, source)


@router.post("/xl", dependencies=[Depends(protect_endpoint)])
async def import_xl(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await process_xl(request, templates, user, source)


@router.post("/fhir", dependencies=[Depends(protect_endpoint)])
async def import_fhir(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await process_fhir(request, templates, user, source)


@router.get("/status", dependencies=[Depends(protect_endpoint)])
async def import_status(
    request: Request,
    page: int,
    size: int,
    filter: str = "",
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    data = {"page": page, "size": size, "filter": filter}
    return templates.TemplateResponse(
        request, "import/status.html", {"user": user, "data": data}
    )


@router.get("/status/data", dependencies=[Depends(protect_endpoint)])
async def import_status_data(
    request: Request,
    page: int,
    size: int,
    filter: str = "",
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    data = FileImport.page(page, size, user.id, session)
    pagination = Pagination(data, "/import/status/data")
    return templates.TemplateResponse(
        request,
        "import/partials/status.html",
        {"user": user, "pagination": pagination, "data": data},
    )


@router.get("/{id}/errors", dependencies=[Depends(protect_endpoint)])
async def import_errors(request: Request, id: str, session: Session = Depends(get_db)):
    user, present_in_db = user_details(request, session)
    data = FileImport.find(id, session)
    files = DataFiles(data.uuid)
    fullpath, filename, exists = files.path("errors")
    if exists:
        return FileResponse(path=fullpath, filename=filename, media_type="text/plain")
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {
                    "error": "Something went wrong downloading the errors file for the import"
                },
            },
        )


@staticmethod
def _import_setup(
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
