import json
from typing import Annotated
from fastapi import APIRouter, Form, Depends, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from simple_error_log import Errors
from usdm4.api.wrapper import Wrapper, StudyVersion, StudyDesign
from usdm4_protocol.m11.views.data_view import DataView
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
        # M11 validation findings were captured during import and
        # persisted as the ``m11_validation`` DataFiles media type (see
        # ``ImportM11.process()``). The compare view just reads that
        # file — it does NOT re-run the validator here. When the file
        # is missing (legacy imports, non-M11 imports) the cell shows
        # empty, which the template renders as "0 findings".
        data["m11_validation"].append(_m11_validation_for_study(usdm))
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


def _m11_validation_for_study(usdm: USDMJson) -> dict[str, list[dict]]:
    """Return the persisted M11 validation findings for a study, grouped
    by element name.

    Findings are captured during M11 import (:class:`ImportM11` in
    ``app/imports/import_processors.py``) by running the DOCX-layer
    validator and persisting the projected rows as the ``m11_validation``
    DataFiles media type. This helper reads that file — it does NOT
    re-run the validator.

    Returns an empty dict when:
      * the import wasn't an M11 (no persisted findings expected),
      * the ``m11_validation`` file is missing (legacy imports written
        before the validator was wired in), or
      * the file can't be read / parsed.

    Callers (the compare view) treat the empty dict as "0 findings" — see
    the namespace counters in ``studies/list.html``.
    """
    if not getattr(usdm, "m11", False):
        return {}
    try:
        files = DataFiles(usdm.uuid)
        full_path, _filename, exists = files.generic_path("m11_validation")
    except Exception:
        return {}
    if not exists:
        return {}
    try:
        with open(full_path, "r") as fh:
            findings = json.load(fh) or []
    except Exception:
        # Degrade to empty — the compare view is not the right place to
        # surface an unexpected read/parse failure.  The persisted file
        # is already projected to the canonical row shape at import
        # time, so no further projection is needed here.
        return {}
    # Group by the ``element`` field so the compare-view template can
    # look up per-cell findings with ``per_study.get(element, [])``.
    # The keys match the title-page dict keys produced by
    # ``DataView.title_page()`` — both sides use the same M11 element
    # names.
    grouped: dict[str, list[dict]] = {}
    for finding in findings:
        grouped.setdefault((finding or {}).get("element") or "", []).append(finding)
    return grouped
