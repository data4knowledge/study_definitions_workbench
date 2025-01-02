from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.model.usdm_json import USDMJson
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import user_details
from app.dependencies.templates import templates

router = APIRouter(
  prefix="/versions",
  tags=["version", "timelines"],
  dependencies=[Depends(protect_endpoint)]
)

@router.get('/{version_id}/studyDesigns/{study_design_id}/timelines', dependencies=[Depends(protect_endpoint)])
async def get_study_design_timelines(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.timelines(study_design_id)
  return templates.TemplateResponse(request, "study_designs/partials/timelines.html", {'user': user, 'data': data})

@router.get('/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/soa', dependencies=[Depends(protect_endpoint)])
async def get_study_design_timeline_soa(request: Request, version_id: int, study_design_id: str, timeline_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.soa(study_design_id, timeline_id)
  return templates.TemplateResponse(request, "timelines/soa.html", {'user': user, 'data': data})

@router.get('/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/export/fhir_soa', dependencies=[Depends(protect_endpoint)])
async def get_study_design_timeline_soa(request: Request, version_id: int, study_design_id: str, timeline_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.soa(study_design_id, timeline_id)
  print("EXPORT SOA")
  return templates.TemplateResponse(request, "timelines/soa.html", {'user': user, 'data': data})
