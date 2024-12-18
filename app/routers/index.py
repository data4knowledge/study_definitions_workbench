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
def index_page(request: Request, page: int, size: int, initial: bool=False, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = {}
  if initial:
    cookie = {
      'phase': [{'selected': True, 'label': x, 'index': i} for i, x in enumerate(Study.phases(user.id, session))],
      'sponsor': [{'selected': True, 'label': x, 'index': i} for i, x in enumerate(Study.sponsors(user.id, session))]
    }
    params = {}
  else:
    cookie_value = request.cookies.get('index_filter')
    cookie = json.loads(cookie_value)
    print(f"ALL: {cookie}")
    all_true = all([x['selected'] for x in cookie['phase']]) and all([x['selected'] for x in cookie['sponsor']])
    print(f"ALL1: {all_true}")
    params = {'phase': [x['label'] for x in cookie['phase'] if x['selected']] , 'sponsor': [x['label'] for x in cookie['sponsor'] if x['selected']]}
    print(f"ALL2: {params}")
    params = params if not all_true else {}
  data['page'] = Study.page(page, size, user.id, params, session)
  data['width'] = 4
  data['index_filter'] = cookie
  print(f"PARAMS: {params}")
  pagination = Pagination(data['page'], "/index/page") 
  response = templates.TemplateResponse(request, "home/partials/page.html", {'user': user, 'pagination': pagination, 'data': data})
  response.set_cookie('index_filter', value=json.dumps(cookie), httponly=True, expires=3600)
  return response

@router.post("/index/filter")
def index_page(request: Request, filter_type: str, id: int, state: bool, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  cookie_value = request.cookies.get('index_filter')
  data = json.loads(cookie_value)
  data[filter_type][id]['selected'] = state
  print(f"FILTER: {filter_type}, {id}, {state}")
  response = templates.TemplateResponse(request, "home/partials/empty.html", {'user': user, 'data': {'index_filter': data}})
  response.set_cookie('index_filter', value=json.dumps(data), httponly=True, expires=3600)
  return response

