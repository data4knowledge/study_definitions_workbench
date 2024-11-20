from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.model.user import User
from app.model.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import is_fhir_tx, user_details
from app.dependencies.templates import templates
from app.model.usdm_json import USDMJson

router = APIRouter(
  prefix="/versions",
  tags=["versions"],
  dependencies=[Depends(protect_endpoint)]
)

@router.get('/{id}/summary')
async def get_version_summary(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  fhir = is_fhir_tx(request)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session), 'fhir': fhir}
  return templates.TemplateResponse(request, "study_versions/summary.html", {'user': user, 'data': data})
