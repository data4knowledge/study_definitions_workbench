from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.model.user import User
from app.model.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import is_fhir_tx, user_details
from app.dependencies.templates import templates
from app.model.usdm_json import USDMJson
from app.dependencies.fhir_version import fhir_versions

router = APIRouter(
  prefix="/versions",
  tags=["versions"],
  dependencies=[Depends(protect_endpoint)]
)

@router.get('/{id}/summary')
async def get_version_summary(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session), 'fhir': {'enabled': is_fhir_tx(request), 'versions': fhir_versions()}}
  return templates.TemplateResponse(request, "study_versions/summary.html", {'user': user, 'data': data})
