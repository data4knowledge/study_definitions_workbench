from typing import Annotated
from fastapi import Form, Depends, FastAPI, Request, BackgroundTasks, HTTPException, status, Form, File
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
from sqlalchemy.orm import Session
from app.utility.background import *
from app.utility.upload import *
from app.model.usdm_json import USDMJson
from app.model.file_import import FileImport
from app import VERSION, SYSTEM_NAME
from app.utility.fhir_version import check_fhir_version
from app.model.database_manager import DatabaseManager as DBM
from app.utility.fhir_service import FHIRService
from app.model.exceptions import FindException

Files.clean_and_tidy()
Files.check()
DBM.check()

app = FastAPI(
  title = SYSTEM_NAME,
  description = "d4k Study Definitions Workbench. The Swiss Army Knife for DDF / USDM Study Definitions",
  version = VERSION
)

@app.exception_handler(Exception)
async def exception_callback(request: Request, exc: Exception):
  return templates.TemplateResponse("errors/error.html", {'request': request, 'data': {'error': f"{exc}"}})

@app.exception_handler(FindException)
async def exception_callback(request: Request, exc: FindException):
  return templates.TemplateResponse("errors/error.html", {'request': request, 'data': {'error': exc.msg}})

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

def protect_endpoint(request: Request) -> None:
  authorisation.protect_route(request, "/login")

def user_details(request: Request, db):
  user_info = request.session['userinfo']
  user, present_in_db = User.check(user_info, db)
  return user, present_in_db

@app.get("/")
def home(request: Request):
  response = templates.TemplateResponse('home/home.html', {'request': request, "version": VERSION})
  return response

@app.get("/login")
async def login(request: Request):
  if not 'id_token' in request.session:  # it could be userinfo instead of id_token
    return await authorisation.login(request, "callback")
  return RedirectResponse("/index")

@app.get("/index", dependencies=[Depends(protect_endpoint)])
def index(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  print(f"INDEX DATA: {user}, {present_in_db}")
  if present_in_db:
    data = Study.page(1, 10, user.id, session)
    #print(f"INDEX DATA: {data}")
    pagination = Pagination(data, "/index") 
    return templates.TemplateResponse("home/index.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})
  else:
    data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'user': User.valid(), 'endpoint': Endpoint.valid()}}
    print(f"INDEX DATA: {data}")
    return templates.TemplateResponse("users/show.html", {'request': request, 'user': user, 'data': data})

@app.get("/users/{id}/show", dependencies=[Depends(protect_endpoint)])
def user_show(request: Request, id: int, session: Session = Depends(get_db)):
  user = User.find(id, session)
  data = {'endpoints': User.endpoints_page(1, 100, user.id, session), 'validation': {'user': User.valid(), 'endpoint': Endpoint.valid()}}
  print(f"USER SHOW: {data}")
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
  data = {'release_notes': ReleaseNotes(os.path.join(templates_path, 'status', 'partials')).notes(), 'system': SYSTEM_NAME, 'version': VERSION}
  return templates.TemplateResponse("about/about.html", {'request': request, 'user': user, 'data': data})

@app.get("/import/m11", dependencies=[Depends(protect_endpoint)])
def import_m11(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return templates.TemplateResponse("import/import_m11.html", {'request': request, 'user': user})

@app.get("/import/xl", dependencies=[Depends(protect_endpoint)])
def import_xl(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return templates.TemplateResponse("import/import_xl.html", {'request': request, 'user': user})

@app.get("/import/fhir", dependencies=[Depends(protect_endpoint)])
def import_fhir(request: Request, version: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  valid, description = check_fhir_version(version)
  if valid:
    data = {'version': version, 'description': description}
    return templates.TemplateResponse("import/import_fhir.html", {'request': request, 'user': user, 'data': data})
  else:
    message = f"Invalid FHIR version '{version}'"
    application_logger.error(message)
    return templates.TemplateResponse('errors/error.html', {"request": request, 'data': {'error': message}})
    
@app.post('/import/m11', dependencies=[Depends(protect_endpoint)])
async def import_m11(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_m11(request, background_tasks, templates, user, session)

@app.post('/import/xl', dependencies=[Depends(protect_endpoint)])
async def import_xl(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_xl(request, background_tasks, templates, user, session)

@app.post('/import/fhir', dependencies=[Depends(protect_endpoint)])
async def import_xl(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_fhir(request, background_tasks, templates, user, session)

@app.get('/import/status', dependencies=[Depends(protect_endpoint)])
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = FileImport.page(page, size, user.id, session)
  pagination = Pagination(data, "/import/status") 
  return templates.TemplateResponse("import/status.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})

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

@app.get('/versions/{id}/export/fhir', dependencies=[Depends(protect_endpoint)])
async def export_fhir(request: Request, id: int, session: Session = Depends(get_db)):
  usdm = USDMJson(id, session)
  full_path, filename, media_type = usdm.fhir()
  if full_path == None:
    return templates.TemplateResponse('errors/error.html', {"request": request, 'data': {'error': f"The study with id '{id}' was not found"}})
  else:
    return FileResponse(path=full_path, filename=filename, media_type=media_type)

@app.get('/versions/{id}/transmit/{endpoint_id}', dependencies=[Depends(protect_endpoint)])
async def get_version_summary(request: Request, id: int, endpoint_id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = usdm.fhir_data()
  endpoint = Endpoint.find(endpoint_id, session)
  application_logger.info(f"Sending FHIR message from study version '{id}' to endpoint: {endpoint.endpoint}")
  server = FHIRService(endpoint.endpoint)
  response = await server.post('Bundle', data, 20.0)
  response = json.dumps(response, indent=2)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session), 'response': response}
  return templates.TemplateResponse('study_versions/transmit.html', {"request": request, 'data': data, 'user': user})

@app.get('/versions/{id}/export/protocol', dependencies=[Depends(protect_endpoint)])
async def export_protocol(request: Request, id: int, session: Session = Depends(get_db)):
  usdm = USDMJson(id, session)
  full_path, filename, media_type = usdm.pdf()
  if full_path == None:
    results = 'Not found'
    return templates.TemplateResponse('errors/partials/error.html', {"request": request, 'data': results})
  else:
    return FileResponse(path=full_path, filename=filename, media_type=media_type)

@app.get("/versions/{id}/protocol", dependencies=[Depends(protect_endpoint)])
async def protocol(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'sections': usdm.protocol_sections()}
  #print(f"PROTOCOL SECTION: {data}")
  response = templates.TemplateResponse('versions/protocol/show.html', {"request": request, "data": data })
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
    # Error here
    application_logger.warning(f"User '{user.id}', '{user.email} attempted to debug the database!")
    return RedirectResponse("/index")

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