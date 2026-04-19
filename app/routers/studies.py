from typing import Annotated
from fastapi import APIRouter, Form, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from simple_error_log import Errors
from usdm4.api.wrapper import Wrapper, StudyVersion, StudyDesign
from usdm4_protocol.m11.views.data_view import DataView
from usdm4_protocol.m11.validate import M11Validator
from app.database.study import Study
from app.database.version import Version
from app.database.file_import import FileImport
from app.database.database import get_db
from app.model.usdm_json import USDMJson
from app.model.file_handling.data_files import DataFiles
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import transmit_role_enabled, user_details
from app.dependencies.templates import templates
from app.utility.template_methods import restructure_study_list
from app.dependencies.fhir_version import fhir_versions

router = APIRouter(
    prefix="/studies", tags=["studies"], dependencies=[Depends(protect_endpoint)]
)


@router.patch("/{id}/select", dependencies=[Depends(protect_endpoint)])
def study_select(
    request: Request,
    id: int,
    action: str,
    list_studies: Annotated[str, Form()] = None,
    session: Session = Depends(get_db),
):
    # data = {}
    user, present_in_db = user_details(request, session)
    selected = True if action.upper() == "SELECT" else False
    parts = list_studies.split(",") if list_studies else []
    parts = [x.strip() for x in parts]
    parts.append(str(id)) if selected else parts.remove(str(id))
    data = {
        "study": Study.summary(id, session),
        "selected": selected,
        "selected_list": (",").join(parts),
    }
    return templates.TemplateResponse(
        request, "studies/partials/select.html", {"user": user, "data": data}
    )


@router.post("/delete", dependencies=[Depends(protect_endpoint)])
def study_delete(
    request: Request,
    delete_studies: Annotated[str, Form()] = None,
    session: Session = Depends(get_db),
):
    # user, present_in_db = user_details(request, session)
    parts = delete_studies.split(",") if delete_studies else []
    for id in parts:
        study = Study.find(id, session)
        imports = study.file_imports(session)
        for im in imports:
            files = DataFiles(im[1])
            files.delete()
            x = FileImport.find(im[0], session)
            x.delete(session)
        study.delete(session)
    return RedirectResponse("/index", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/list", dependencies=[Depends(protect_endpoint)])
def study_list(
    request: Request, list_studies: str = None, session: Session = Depends(get_db)
):
    user, present_in_db = user_details(request, session)
    parts = list_studies.split(",") if list_studies else []
    data = {
        "m11_title_page": [],
        # M11 validation findings per study, grouped by element name. Parallel
        # list (same index as m11_title_page pre-transpose / same column as
        # the rendered comparison table post-transpose). Not transposed here
        # because by_element() dicts from different studies can have
        # different key sets; the template indexes positionally instead.
        "m11_validation": [],
        "inclusion": [],
        "exclusion": [],
        "m11_amendment_details": [],
    }
    for id in parts:
        version = Version.find_latest_version(id, session)
        usdm = USDMJson(version.id, session)
        wrapper: Wrapper = usdm.wrapper()
        study_version: StudyVersion = wrapper.first_version()
        study_design: StudyDesign = study_version.studyDesigns[0]
        errors = Errors()
        m11 = DataView(wrapper, errors)
        data["m11_title_page"].append(m11.title_page())
        # Run M11 validation against the same Wrapper the compare view is
        # already displaying. Fast (no docx extraction — wrapper is already
        # loaded). Convert Findings to dicts here so the Jinja template
        # can stay attribute-style without importing Finding.
        #
        # Rehydrate the errors from the original import so that
        # extraction-time normalisation + contradiction records survive
        # into this view. Without this, the compare view would be
        # Wrapper-state only and findings that the extractor silently
        # reconciled (e.g. Amendment Identifier contradictions on
        # original protocols) never surface here.
        validation_errors = usdm.import_errors()
        validation = M11Validator(wrapper, validation_errors).validate()
        data["m11_validation"].append(
            {k: [f.to_dict() for f in v] for k, v in validation.by_element().items()}
        )
        ie_map = study_version.eligibility_critieria_item_map()
        data["inclusion"].append(study_design.inclusion_criteria(ie_map))
        data["exclusion"].append(study_design.exclusion_criteria(ie_map))
    data["m11_title_page"] = restructure_study_list(data["m11_title_page"])
    data["fhir"] = {
        "enabled": transmit_role_enabled(request),
        "versions": fhir_versions(),
    }
    print(f"DATA: {data}")
    return templates.TemplateResponse(
        request, "studies/list.html", {"user": user, "data": data}
    )
