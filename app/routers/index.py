#from typing import Annotated
from fastapi import APIRouter, Form, Depends, Request
from sqlalchemy.orm import Session
from app.database.study import Study
from d4kms_ui.pagination import Pagination
#from app.database.endpoint import Endpoint
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
#from app.dependencies.utility import is_admin
from app.dependencies.templates import templates
from app.dependencies.utility import is_fhir_tx, user_details
from app.dependencies.fhir_version import fhir_versions
#from d4kms_generic.logger import application_logger

router = APIRouter(
  prefix="",
  tags=["index"],
  dependencies=[Depends(protect_endpoint)]
)

@router.get("/index")
def index(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  fhir = {'enabled': is_fhir_tx(request), 'versions': fhir_versions()}
  if present_in_db or user:
    data = {'fhir': fhir}
    return templates.TemplateResponse(request, "home/index.html", {'user': user, 'data': data})
  else:
    return templates.TemplateResponse(request, 'errors/error.html', {'user': None, 'data': {'error': "Unable to determine user."}})
  
@router.get("/index/page")
def index_page(request: Request, page: int, size: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = Study.page(page, size, user.id, session)
  data['width'] = 4
  pagination = Pagination(data, "/index/page") 
  return templates.TemplateResponse(request, "home/partials/page.html", {'user': user, 'pagination': pagination, 'data': data})
