import json
from fastapi import APIRouter, Form, Depends, Request
from sqlalchemy.orm import Session
from app.database.study import Study
from d4kms_ui.pagination import Pagination
from app.database.database import get_db
from app.dependencies.dependency import protect_endpoint
from app.dependencies.templates import templates
from app.dependencies.utility import is_fhir_tx, user_details
from app.dependencies.fhir_version import fhir_versions

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
  data = {}
  data['page'] = Study.page(page, size, user.id, {}, session)
  data['width'] = 4
  
  # data['index_filter'] = {
  #   'phases': [{'selected': False, 'label': x, 'index': i} for i, x in enumerate(Study.phases(user.id, session))],
  #   'sponsors': [{'selected': False, 'label': x, 'index': i} for i, x in enumerate(Study.sponsors(user.id, session))]
  # }
  
  cookie = {
    'phase': [{'selected': False, 'label': x, 'index': i} for i, x in enumerate(Study.phases(user.id, session))],
    'sponsor': [{'selected': False, 'label': x, 'index': i} for i, x in enumerate(Study.sponsors(user.id, session))]
  }
  print(f"POSS COOKIE: {cookie}")
  data['index_filter'] = cookie

  phases = []
  sponsors = []
  for index, label in enumerate(Study.phases(user.id, session)):
    phases.append({'selected': False, 'label': label, 'index': index})
  for index, label in enumerate(Study.sponsors(user.id, session)):
    sponsors.append({'selected': False, 'label': label, 'index': index})

  pagination = Pagination(data['page'], "/index/page") 
  response = templates.TemplateResponse(request, "home/partials/page.html", {'user': user, 'pagination': pagination, 'data': data})

  #response.set_cookie('index_filter', value={'phases': phases, 'sponsors': sponsors}, httponly=True, expires=3600)
  response.set_cookie('index_filter', value=json.dumps(cookie), httponly=True, expires=3600)
  return response

@router.get("/index/filter")
def index_page(request: Request, filter_type: str, id: int, state: bool, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  
  print(f"FILTER: {filter_type}, {id}, {state}")
  
  cookie_value = request.cookies.get('index_filter')
  #print(f"COOKIE: {cookie_value}")
  xxx = json.loads(cookie_value)
  #print(f"VALUE: {xxx} {type(xxx)}")
  #x = xxx[filter_type]
  #y = x[id]
  xxx[filter_type][id]['selected'] = state
  print(f"FILTER: {xxx[filter_type]}")
  
  data = {'index_filter': xxx}
  response = templates.TemplateResponse(request, "home/partials/filter.html", {'user': user, 'data': data})
  response.set_cookie('index_filter', value=json.dumps(xxx), httponly=True, expires=3600)
  return response
