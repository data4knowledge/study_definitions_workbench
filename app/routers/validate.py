from fastapi import APIRouter, Depends, Request
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
from usdm4 import USDM4, RulesValidationResults
from usdm3 import USDM3
from usdm4_protocol.m11 import USDM4M11

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
    return _validate_setup(
        request,
        session,
        "json",
        False,
        "/validate/usdm",
        "validate/partials/validate_json.html",
        {"version": usdm_version},
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
    user, present_in_db = user_details(request, session)
    return await _process(request, user, USDM4(), source)


@router.get("/m11-docx", dependencies=[Depends(protect_endpoint)])
def validate_m11_docx(request: Request, session: Session = Depends(get_db)):
    """File picker for M11 ``.docx`` validation. Extracts the protocol via
    USDM4M11 then runs the M11 specification checks."""
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


@staticmethod
async def _process(request: Request, user: User, usdm: USDM3 | USDM4, source: str):
    form_handler = FormHandler(
        request,
        False,
        ".json",
        source,
    )
    main_file, image_files, messages = await form_handler.get_files()
    # print(f"MAIN FILE: {main_file['filename']}")
    if main_file:
        files = DataFiles()
        _ = files.new()
        files.save("usdm", main_file["contents"], main_file["filename"])
        full_path, filename, exists = files.path("usdm")
        results: RulesValidationResults = usdm.validate(full_path)
        errors = results.to_dict()
        files.delete()
    else:
        print(f"Messages: {messages}")
        errors = []
        messages.append("Failed to process the validation file")
    return templates.TemplateResponse(
        request,
        "validate/partials/results.html",
        {
            "user": user,
            "data": {
                "filename": main_file,
                "messages": messages,
                "errors": errors,
            },
        },
    )


@staticmethod
async def _process_m11_docx(request: Request, user: User, source: str):
    """Process an uploaded M11 ``.docx`` through USDM4M11 validation and
    render the findings template.

    Mirrors ``_process`` for USDM JSON. Differences: ``.docx`` extension,
    USDM4M11 entry point, and a different results partial because M11
    findings carry element + section location rather than klass/attribute.
    """
    form_handler = FormHandler(
        request,
        False,
        ".docx",
        source,
    )
    main_file, image_files, messages = await form_handler.get_files()
    findings: list[dict] = []
    if main_file:
        files = DataFiles()
        _ = files.new()
        # Reuse the existing "docx" media type; "m11" isn't registered in
        # DataFiles.media_type and shouldn't be added just for validation.
        files.save("docx", main_file["contents"], main_file["filename"])
        full_path, filename, exists = files.path("docx")
        m11 = USDM4M11()
        results = m11.validate_docx(full_path)
        if results is None:
            messages.append("Validation could not be completed (extraction failed).")
        else:
            findings = results.to_dict()
        files.delete()
    else:
        messages.append("Failed to process the validation file")
    return templates.TemplateResponse(
        request,
        "validate/partials/m11_docx_results.html",
        {
            "user": user,
            "data": {
                "filename": main_file,
                "messages": messages,
                "findings": findings,
            },
        },
    )
