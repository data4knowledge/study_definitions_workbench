
from typing import Annotated
from fastapi import Form, Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from d4kms_generic.auth0_service import Auth0Service
from d4kms_generic import application_logger
from d4kms_ui.release_notes import ReleaseNotes
from d4kms_ui.pagination import Pagination
from app.model.database import get_db
from app.model.user import User
from app.model.version import Version
from app.model.file_import import FileImport
from app.model.endpoint import Endpoint
from app.model.user_endpoint import UserEndpoint
from app.model.transmission import Transmission
from app.model.connection_manager import connection_manager
from sqlalchemy.orm import Session
from app.utility.background import *
from app.utility.upload import *
from app.utility.template_methods import *
from app.utility.environment import single_user, file_picker
from app.model.usdm_json import USDMJson
from app.model.file_import import FileImport
from app import VERSION, SYSTEM_NAME
from app.utility.fhir_version import check_fhir_version, fhir_version_description
from app.utility.fhir_transmit import run_fhir_transmit
from app.model.database_manager import DatabaseManager as DBM
from app.model.exceptions import FindException
from usdm_model.wrapper import Wrapper
from app.model.usdm.m11.title_page import USDMM11TitlePage
from app.model.file_handling.pfda.pfda import PFDA
from app.model.file_handling.local_files import LocalFiles

DataFiles.clean_and_tidy()
DataFiles.check()
DBM.check()

app = FastAPI(
  title = SYSTEM_NAME,
  description = "d4k Study Definitions Workbench. The Swiss Army Knife for DDF / USDM Study Definitions",
  version = VERSION
)

@app.exception_handler(Exception)
async def exception_callback(request: Request, exc: Exception):
  RedirectResponse(f"/", status_code=303)

@app.exception_handler(FindException)
async def exception_callback(request: Request, exc: FindException):
  RedirectResponse(f"/", status_code=303)

application_logger.set_level(application_logger.DEBUG)
application_logger.info(f"Starting {SYSTEM_NAME}")

dir_path = os.path.dirname(os.path.realpath(__file__))
templates_path = os.path.join(dir_path, "templates")
static_path = os.path.join(dir_path, "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)
application_logger.info(f"Template dir set to '{templates_path}'")
application_logger.info(f"Static dir set to '{static_path}'")

authorisation = Auth0Service(app)
authorisation.register()

templates.env.globals['server_name'] = server_name
templates.env.globals['single_multiple'] = single_multiple
templates.env.globals['fhir_version_description'] = fhir_version_description
templates.env.globals['title_page_study_list_headings'] = title_page_study_list_headings

single = single_user()
application_logger.info(f'Single user mode: {single}')

def protect_endpoint(request: Request) -> None:
  if single:
    request.session['userinfo'] = {'email': '', 'sub': 'SUE|1234567890', 'nickname': 'Single User'}
    return None
  else:
    authorisation.protect_route(request, "/login")

def user_details(request: Request, db):
  user_info = request.session['userinfo']
  user, present_in_db = User.check(user_info, db)
  #application_logger.info(f"User details {user}")
  return user, present_in_db

@app.websocket("/alerts/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
  await connection_manager.connect(user_id, websocket)
  try:
    while True:
      await websocket.receive_text()
  except WebSocketDisconnect:
      connection_manager.disconnect(user_id)

@app.get("/")
def home(request: Request):
  response = templates.TemplateResponse('home/home.html', {'request': request, "version": VERSION})
  return response

@app.get("/login")
async def login(request: Request):
  if single:
    return RedirectResponse("/index")
  else:
    if not 'id_token' in request.session:  # it could be userinfo instead of id_token
      return await authorisation.login(request, "callback")
    return RedirectResponse("/index")

@app.get("/index", dependencies=[Depends(protect_endpoint)])
def index(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  if present_in_db:
    data = Study.page(1, 10, user.id, session)
    #print(f"INDEX DATA: {data}")
    pagination = Pagination(data, "/index") 
    return templates.TemplateResponse("home/index.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})
  else:
    data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'user': User.valid(), 'endpoint': Endpoint.valid()}, 'debug': {'level': application_logger.get_level_str()}}
    #print(f"INDEX DATA: {data}")
    return templates.TemplateResponse("users/show.html", {'request': request, 'user': user, 'data': data})

@app.patch("/studies/{id}/select", dependencies=[Depends(protect_endpoint)])
def study_select(request: Request, id: int, action: str, list_studies: Annotated[str, Form()]=None, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  selected = True if action.upper() == 'SELECT' else False
  parts = list_studies.split(',') if list_studies else []
  parts.append(str(id)) if selected else parts.remove(str(id))
  data = {'study': Study.summary(id, session), 'selected': selected, 'selected_list': (',').join(parts)}
  #print(f"DATA: {data}")
  return templates.TemplateResponse("studies/partials/select.html", {'request': request, 'user': user, 'data': data})

@app.post("/studies/delete", dependencies=[Depends(protect_endpoint)])
def study_delete(request: Request, delete_studies: Annotated[str, Form()]=None, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  parts = delete_studies.split(',') if delete_studies else []
  for id in parts:
    study = Study.find(id, session)
    imports = study.file_imports(session)
    for im in imports:
      #print(f"IM: {im}, id={im[0]}, uuid={im[1]}")
      files = Files(im[1])
      files.delete()
      x = FileImport.find(im[0], session)
      x.delete(session)
    study.delete(session)
    #print(f"STUDY DELETE: {imports}")
  return RedirectResponse("/index", status_code=303)

@app.get("/studies/list", dependencies=[Depends(protect_endpoint)])
def study_list(request: Request, list_studies: str=None, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  #print(f"STUDIES: {list_studies}")
  parts = list_studies.split(',') if list_studies else []
  data = []
  for id in parts:
    version = Version.find_latest_version(id, session)
    usdm = USDMJson(version.id, session)
    m11 = USDMM11TitlePage(usdm.wrapper(), usdm.extra())
    data.append(m11.__dict__)
  data = restructure_study_list(data)
  #print(f"STUDY LIST: {data}")
  return templates.TemplateResponse("studies/list.html", {'request': request, 'user': user, 'data': data})

@app.get("/users/{id}/show", dependencies=[Depends(protect_endpoint)])
def user_show(request: Request, id: int, session: Session = Depends(get_db)):
  user = User.find(id, session)
  data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'user': User.valid(), 'endpoint': Endpoint.valid()}, 'debug': {'level': application_logger.get_level_str()}}
  print(f"DATA SHOW: {data}")
  return templates.TemplateResponse("users/show.html", {'request': request, 'user': user, 'data': data})
  
@app.post("/users/{id}/displayName", dependencies=[Depends(protect_endpoint)])
def user_display_name(request: Request, id: int, name: Annotated[str, Form()], session: Session = Depends(get_db)):
  user = User.find(id, session)
  updated_user, validation = user.update_display_name(name, session)
  use_user = updated_user if updated_user else user
  data = {'validation': {'user': validation}}
  #print(f"UPDATE DISPLAY NAME: {data}")
  return templates.TemplateResponse(f"users/partials/display_name.html", {'request': request, 'user': use_user, 'data': data})
  
@app.post("/users/{id}/endpoint", dependencies=[Depends(protect_endpoint)])
def user_endpoint(request: Request, id: int, name: Annotated[str, Form()], url: Annotated[str, Form()], session: Session = Depends(get_db)):
  user = User.find(id, session)
  endpoint, validation = Endpoint.create(name, url, "FHIR", user.id, session)
  data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'endpoint': validation}}
  #print(f"UPDATE ENDPOINT: {data}")
  return templates.TemplateResponse(f"users/partials/endpoint.html", {'request': request, 'user': user, 'data': data})

@app.delete("/users/{id}/endpoint/{endpoint_id}", dependencies=[Depends(protect_endpoint)])
def user_endpoint(request: Request, id: int, endpoint_id: int, session: Session = Depends(get_db)):
  user = User.find(id, session)
  endpoint = Endpoint.find(endpoint_id, session)
  endpoint.delete(user.id, session)
  data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'endpoint': Endpoint.valid()}}
  return templates.TemplateResponse(f"users/partials/endpoint.html", {'request': request, 'user': user, 'data': data})

@app.get("/about", dependencies=[Depends(protect_endpoint)])
def about(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  rn = ReleaseNotes(os.path.join(templates_path, 'status', 'partials'))
  data = {'release_notes': rn.notes(), 'system': SYSTEM_NAME, 'version': VERSION}
  return templates.TemplateResponse("about/about.html", {'request': request, 'user': user, 'data': data})

@app.get("/flieList", dependencies=[Depends(protect_endpoint)])
def about(request: Request, dir: str = None, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  picker = file_picker()
  valid, data, message = PFDA().dir(dir) if picker['pfda'] else LocalFiles().dir(dir)
  if valid:
    return templates.TemplateResponse("import/partials/file_list.html", {'request': request, 'user': user, 'data': data})
  else:
    application_logger.error(message)
    return templates.TemplateResponse('errors/partials/error.html', {"request": request, 'data': {'error': message}})

@app.get("/import/m11", dependencies=[Depends(protect_endpoint)])
def import_m11(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = file_picker()
  return templates.TemplateResponse("import/import_m11.html", {'request': request, 'user': user, 'data': data})

@app.get("/import/xl", dependencies=[Depends(protect_endpoint)])
def import_xl(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = file_picker()
  return templates.TemplateResponse("import/import_xl.html", {'request': request, 'user': user, 'data': data})

@app.get("/import/fhir", dependencies=[Depends(protect_endpoint)])
def import_fhir(request: Request, version: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  valid, description = check_fhir_version(version)
  if valid:
    data = file_picker()
    data['version'] = version
    data['description'] = description
    return templates.TemplateResponse("import/import_fhir.html", {'request': request, 'user': user, 'data': data})
  else:
    message = f"Invalid FHIR version '{version}'"
    application_logger.error(message)
    return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': message}})
    
@app.post('/import/m11', dependencies=[Depends(protect_endpoint)])
async def import_m11(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_m11(request, templates, user)

@app.post('/import/m11/pfda', dependencies=[Depends(protect_endpoint)])
async def import_m11_pfda(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_m11(request, templates, user, source='pfda')

@app.post('/import/xl', dependencies=[Depends(protect_endpoint)])
async def import_xl(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_xl(request, templates, user)

@app.post('/import/fhir', dependencies=[Depends(protect_endpoint)])
async def import_fhir(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_fhir(request, templates, user)

@app.get('/import/status', dependencies=[Depends(protect_endpoint)])
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = {'page': page, 'size': size, 'filter': filter} 
  return templates.TemplateResponse("import/status.html", {'request': request, 'user': user, 'data': data})

@app.get('/import/status/data', dependencies=[Depends(protect_endpoint)])
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = FileImport.page(page, size, user.id, session)
  pagination = Pagination(data, "/import/status/data") 
  return templates.TemplateResponse("import/partials/status.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})

@app.get('/import/{id}/errors', dependencies=[Depends(protect_endpoint)])
async def import_status(request: Request, id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = FileImport.find(id, session)
  files = Files(data.uuid)
  fullpath, filename, exists = files.path('errors')
  if exists:
    return FileResponse(path=fullpath, filename=filename, media_type='text/plain')
  else:
    return templates.TemplateResponse("errors/error.html", {'request': request, 'user': user, 'data': {'error': 'Something went wrong downloading the errors file for the import'}})

@app.get('/transmissions/status', dependencies=[Depends(protect_endpoint)])
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  # data = Transmission.page(page, size, user.id, session)
  # pagination = Pagination(data, "/transmissions/status")
  data = {'page': page, 'size': size, 'filter': filter} 
  return templates.TemplateResponse("transmissions/status.html", {'request': request, 'user': user, 'data': data})

@app.get('/transmissions/status/data', dependencies=[Depends(protect_endpoint)])
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = Transmission.page(page, size, user.id, session)
  pagination = Pagination(data, "/transmissions/status/data")
  return templates.TemplateResponse("transmissions/partials/status.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})

@app.get('/versions/{id}/summary', dependencies=[Depends(protect_endpoint)])
async def get_version_summary(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session)}
  #print(f"VERSION SUMMARY DATA: {data}")
  return templates.TemplateResponse("study_versions/summary.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/summary', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
  return templates.TemplateResponse("study_designs/summary.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/overallParameters', dependencies=[Depends(protect_endpoint)])
async def get_study_design_o_parameters(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_overall_parameters(study_design_id)
  #print(f"OVERALL SUMMARY DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/overall_parameters.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/designParameters', dependencies=[Depends(protect_endpoint)])
async def get_study_design_d_parameters(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_design_parameters(study_design_id)
  #print(f"DESIGN PARAMETERS DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/design_parameters.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/schema', dependencies=[Depends(protect_endpoint)])
async def get_study_design_schema(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_schema(study_design_id)
  #print(f"SCHEMA DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/schema.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/interventions', dependencies=[Depends(protect_endpoint)])
async def get_study_design_interventions(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_interventions(study_design_id)
  #print(f"INTERVENTION DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/interventions.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/estimands', dependencies=[Depends(protect_endpoint)])
async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_estimands(study_design_id)
  #print(f"ESTIMAND DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/estimands.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{id}/safety', dependencies=[Depends(protect_endpoint)])
async def get_version_safety(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session)}
  #print(f"VERSION SUMMARY DATA: {data}")
  return templates.TemplateResponse("study_versions/safety.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/safety', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
  return templates.TemplateResponse("study_designs/safety.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/aeSpecialInterest', dependencies=[Depends(protect_endpoint)])
async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.adverse_events_special_interest(study_design_id)
  #print(f"AE SPECIAL INTEREST DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/ae_special_interest.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/safetyAssessments', dependencies=[Depends(protect_endpoint)])
async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.safety_assessments(study_design_id)
  #print(f"SAFETY ASSESSMENT DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/safety_assessments.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{id}/statistics', dependencies=[Depends(protect_endpoint)])
async def get_version_statistics(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session)}
  #print(f"VERSION SUMMARY DATA: {data}")
  return templates.TemplateResponse("study_versions/statistics.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/statistics', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
  return templates.TemplateResponse("study_designs/statistics.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/sampleSize', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.sample_size(study_design_id)
  #print(f"SAMPLE SIZE DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/sample_size.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/analysisSets', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.analysis_sets(study_design_id)
  ###print(f"ANALYSIS SETS DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/analysis_sets.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/analysisObjective', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.analysis_objectives(study_design_id)
  #print(f"ANALYSIS OBJECTIVES DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/analysis_objective.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{id}/export/fhir', dependencies=[Depends(protect_endpoint)])
async def export_fhir(request: Request, id: int, version: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  valid, description = check_fhir_version(version)
  if valid:
    full_path, filename, media_type = usdm.fhir(version.upper())
    if full_path:
      return FileResponse(path=full_path, filename=filename, media_type=media_type)
    else:
      return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"The study with id '{id}' was not found."}})
  else:
    return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"Invalid FHIR M11 message version export requested. Version requested was '{version}'."}})

@app.get('/versions/{id}/transmit/{endpoint_id}', dependencies=[Depends(protect_endpoint)])
async def version_transmit(request: Request, id: int, endpoint_id: int, version: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  valid, description = check_fhir_version(version)
  if valid:
    run_fhir_transmit(id, endpoint_id, version, user)
    return RedirectResponse(f'/versions/{id}/summary')
  else:
    return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"Invalid FHIR M11 message version trsnsmission requested. Version requested was '{version}'."}})

@app.get('/versions/{id}/export/json', dependencies=[Depends(protect_endpoint)])
async def export_json(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  full_path, filename, media_type = usdm.json()
  if full_path:
    return FileResponse(path=full_path, filename=filename, media_type=media_type)
  else:
    return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"Error downloading the requested JSON file"}})

@app.get('/versions/{id}/export/protocol', dependencies=[Depends(protect_endpoint)])
async def export_protocol(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  full_path, filename, media_type = usdm.pdf()
  if full_path:
    return FileResponse(path=full_path, filename=filename, media_type=media_type)
  else:
    return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"Error downloading the requested PDF file"}})

@app.get("/versions/{id}/protocol", dependencies=[Depends(protect_endpoint)])
async def protocol(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'sections': usdm.protocol_sections(), 'section_list': usdm.protocol_sections_list()}
  #print(f"PROTOCOL SECTION: {data}")
  response = templates.TemplateResponse('versions/protocol/show.html', {"request": request, "data": data, 'user': user})
  return response

@app.get("/versions/{id}/section/{section_id}", dependencies=[Depends(protect_endpoint)])
async def protocl_section(request: Request, id: int, section_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'section': usdm.section(section_id)}
  response = templates.TemplateResponse('versions/protocol//partials/section.html', {"request": request, "data": data })
  return response

@app.get('/database/clean', dependencies=[Depends(protect_endpoint)])
async def database_clean(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  if user.email == "daveih1664dk@gmail.com":
    database_managr = DBM(session)
    database_managr.clear_all()
    endpoint, validation = Endpoint.create('LOCAL TEST', 'http://localhost:8010/m11', "FHIR", user.id, session)
    endpoint, validation = Endpoint.create('Hugh Server', 'https://fs-01.azurewebsites.net', "FHIR", user.id, session)
    endpoint, validation = Endpoint.create('HAPI Server', 'https://hapi.fhir.org/baseR5', "FHIR", user.id, session)
    application_logger.info(f"User '{user.id}', '{user.email} cleared the database")
  else:
    # Error here
    application_logger.warning(f"User '{user.id}', '{user.email} attempted to clear the database!")
  return RedirectResponse("/index")

@app.get("/database/debug", dependencies=[Depends(protect_endpoint)])
async def database_clean(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  if user.email == "daveih1664dk@gmail.com":
    data = {}
    data['users'] = json.dumps(User.debug(session), indent=2)
    data['studies'] = json.dumps(Study.debug(session), indent=2)
    data['versions'] = json.dumps(Version.debug(session), indent=2)
    data['imports'] = json.dumps(FileImport.debug(session), indent=2)
    data['endpoints'] = json.dumps(Endpoint.debug(session), indent=2)
    data['user_endpoints'] = json.dumps(UserEndpoint.debug(session), indent=2)
    response = templates.TemplateResponse('database/debug.html', {'request': request, 'user': user, 'data': data})
    return response
  else:
    await connection_manager.error(f"Operation request denied", str(user.id))
    application_logger.error(f"User '{user.id}', '{user.email} attempted to debug the database!")
    return RedirectResponse(f"/users/{user.id}/show", status_code=303)

@app.patch("/debug", dependencies=[Depends(protect_endpoint)])
async def debug_level(request: Request, level: str='INFO', session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  if user.email == "daveih1664dk@gmail.com" and level.upper() in ['DEBUG', 'INFO']:
    level = application_logger.DEBUG if level.upper() == 'DEBUG' else application_logger.INFO
    application_logger.set_level(level)
    return templates.TemplateResponse('users/partials/debug.html', {'request': request, 'user': user, 'data': {'debug': {'level': application_logger.get_level_str()}}})
  else:
    await connection_manager.error(f"Operation request denied", str(user.id))
    application_logger.error(f"User '{user.id}', '{user.email} attempted to change debug level!")
    return templates.TemplateResponse('users/partials/debug.html', {'request': request, 'user': user, 'data': {'debug': {'level': application_logger.get_level_str()}}})

@app.get("/logout")
def logout(request: Request):
  url = authorisation.logout(request, "home")
  return RedirectResponse(url=url)

@app.get("/callback")
async def callback(request: Request):
  try:
    await authorisation.save_token(request)
    return RedirectResponse("/index")
  except:
    return RedirectResponse("/logout")