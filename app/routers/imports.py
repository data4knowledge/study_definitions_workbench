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
from d4k_ms_base.logger import application_logger
from d4k_ms_ui.pagination import Pagination
from app.database.file_import import FileImport
from app.imports.request_handler import RequestHandler
from app.imports.import_manager import ImportManager
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


@router.get("/usdm", dependencies=[Depends(protect_endpoint)])
def import_usdm(request: Request, session: Session = Depends(get_db)):
    return _import_setup(
        request,
        session,
        "json",
        False,
        "/import/usdm",
        "import/import_json.html",
        {"version": usdm_version},
    )


@router.get("/m11-docx", dependencies=[Depends(protect_endpoint)])
def import_m11_docx(request: Request, session: Session = Depends(get_db)):
    return _import_setup(
        request, session, "docx", False, "/import/m11", "import/import_m11_docx.html"
    )


@router.get("/cpt-docx", dependencies=[Depends(protect_endpoint)])
def import_cpt_docx(request: Request, session: Session = Depends(get_db)):
    return _import_setup(
        request, session, "docx", False, "/import/m11", "import/import_cpt_docx.html"
    )


@router.get("/legacy-pdf", dependencies=[Depends(protect_endpoint)])
def import_legacy_docx(request: Request, session: Session = Depends(get_db)):
    return _import_setup(
        request, session, "pdf", False, "/import/m11", "import/import_legacy_pdf.html"
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
async def import_m11_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await RequestHandler(ImportManager.M11_DOCX, source).process(
        request, templates, user
    )


@router.post("/cpt-docx", dependencies=[Depends(protect_endpoint)])
async def import_cpt_docx_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await RequestHandler(ImportManager.CPT_DOCX, source).process(
        request, templates, user
    )


@router.post("/legacy-pdf", dependencies=[Depends(protect_endpoint)])
async def import_legacy_pdf__process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await RequestHandler(ImportManager.LEGACY_PDF, source).process(
        request, templates, user
    )


@router.post("/xl", dependencies=[Depends(protect_endpoint)])
async def import_xl_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await RequestHandler(ImportManager.USDM_EXCEL, source).process(
        request, templates, user
    )


@router.post("/fhir", dependencies=[Depends(protect_endpoint)])
async def import_fhir_process(
    request: Request, version: str, source: str = "browser", session: Session = Depends(get_db)
):
    application_logger.info(f"FHIR version: {version}")
    user, present_in_db = user_details(request, session)
    request_version = ImportManager.FHIR_PRISM3_JSON if version == "p3" else ImportManager.FHIR_PRISM2_JSON
    return await RequestHandler(request_version, source).process(
        request, templates, user
    )


@router.post("/usdm3", dependencies=[Depends(protect_endpoint)])
async def import_usdm3_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await RequestHandler(ImportManager.USDM3_JSON, source).process(
        request, templates, user
    )


@router.post("/usdm", dependencies=[Depends(protect_endpoint)])
async def import_usdm_process(
    request: Request, source: str = "browser", session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    return await RequestHandler(ImportManager.USDM4_JSON, source).process(
        request, templates, user
    )


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
    # print(f"********** Data: {data}")
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
