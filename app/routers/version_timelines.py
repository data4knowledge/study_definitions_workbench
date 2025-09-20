from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database.user import User
from app.database.database import get_db
from app.model.usdm_json import USDMJson
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import user_details, transmit_role_enabled
from app.dependencies.templates import templates
from app.utility.fhir_transmit import run_fhir_soa_transmit
from usdm4_pj import USDM4PJ 


router = APIRouter(
    prefix="/versions",
    tags=["version", "timelines"],
    dependencies=[Depends(protect_endpoint)],
)


@router.get(
    "/{version_id}/studyDesigns/{study_design_id}/timelines",
    dependencies=[Depends(protect_endpoint)],
)
async def get_study_design_timelines(
    request: Request,
    version_id: int,
    study_design_id: str,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(version_id, session)
    data = usdm.timelines(study_design_id)
    # print(f"DATA: {data}")
    return templates.TemplateResponse(
        request, "study_designs/partials/timelines.html", {"user": user, "data": data}
    )


@router.get(
    "/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/soa",
    dependencies=[Depends(protect_endpoint)],
)
async def get_study_design_timeline_soa(
    request: Request,
    version_id: int,
    study_design_id: str,
    timeline_id: str,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(version_id, session)
    data = usdm.soa(study_design_id, timeline_id)
    data["fhir"] = {"enabled": transmit_role_enabled(request)}
    data["endpoints"] = User.endpoints_page(1, 100, user.id, session)
    # print(f"DATA: {data}")
    return templates.TemplateResponse(
        request, "timelines/soa.html", {"user": user, "data": data}
    )


@router.get(
    "/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/export/fhir",
    dependencies=[Depends(protect_endpoint)],
)
async def get_study_design_timeline_soa(
    request: Request,
    version_id: int,
    study_design_id: str,
    timeline_id: str,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(version_id, session)
    full_path, filename, media_type = usdm.fhir_soa(timeline_id)
    if full_path:
        return FileResponse(path=full_path, filename=filename, media_type=media_type)
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {
                    "error": "Error downloading the requested FHIR SoA message file"
                },
            },
        )


@router.get(
    "/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/export/pj", 
    dependencies=[Depends(protect_endpoint)]
)
async def export_patient_journey(    request: Request,
    version_id: int,
    study_design_id: str,
    timeline_id: str,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    usdm = USDMJson(version_id, session)
    df = usdm._files
    full_path, filename, media_type = df.path("usdm")
    if full_path:
        pj = USDM4PJ()
        pj.from_usdm4(full_path)
        print(f"ERRORS: {pj.success}, {pj.fatal_error}, {pj._errors.dump(0)}")
        data = pj.patient_journey
        print(f"JSON: {data}")
        pj_path, pj_filename = df.save("pj", data)
        print(f"FILES: {pj_path}, {pj_filename}")
        return FileResponse(path=pj_path, filename=pj_filename, media_type="text/plain")
    else:
        return templates.TemplateResponse(
            request,
            "errors/error.html",
            {
                "user": user,
                "data": {"error": "Error downloading the requested JSON file"},
            },
        )

@router.get(
    "/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/transmit/{endpoint_id}",
    dependencies=[Depends(protect_endpoint)],
)
async def get_study_design_timeline_soa(
    request: Request,
    version_id: int,
    study_design_id: str,
    timeline_id: str,
    endpoint_id: str,
    session: Session = Depends(get_db),
):
    user, present_in_db = user_details(request, session)
    run_fhir_soa_transmit(version_id, endpoint_id, timeline_id, user)
    return RedirectResponse(
        f"/versions/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/soa"
    )
