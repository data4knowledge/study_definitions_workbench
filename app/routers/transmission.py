from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.model.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.utility import is_fhir_tx, user_details
from app.dependencies.templates import templates
from app.model.transmission import Transmission
from d4kms_ui.pagination import Pagination

router = APIRouter(
  prefix="/transmissions",
  tags=["transmissions"],
  dependencies=[Depends(protect_endpoint)]
)

@router.get('/transmissions/status')
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  if is_fhir_tx(request):
    data = {'page': page, 'size': size, 'filter': filter} 
    return templates.TemplateResponse(request, "transmissions/status.html", {'user': user, 'data': data})
  else:
    return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': "User is not authorised to transmit FHIR messages."}})


@router.get('/transmissions/status/data')
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  if is_fhir_tx(request):
    data = Transmission.page(page, size, user.id, session)
    pagination = Pagination(data, "/transmissions/status/data")
    return templates.TemplateResponse(request, "transmissions/partials/status.html", {'user': user, 'pagination': pagination, 'data': data})
  else:
    return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': "User is not authorised to transmit FHIR messages."}})
