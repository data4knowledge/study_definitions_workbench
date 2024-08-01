from fastapi import Depends, FastAPI, Request, BackgroundTasks, HTTPException, status, Form, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from d4kms_generic.auth0_service import Auth0Service
from d4kms_generic import application_logger
from d4kms_ui.release_notes import ReleaseNotes
from d4kms_ui.pagination import Pagination
from model.database import SessionLocal, engine, get_db
from model.user import User
from model.version import Version
from model.file_import import FileImport
from sqlalchemy.orm import Session
from model import models
from utility.background import *
from utility.upload import *
from model.usdm_json import USDMJson
from model.file_import import FileImport
from model import VERSION, SYSTEM_NAME

app = FastAPI(
  title = SYSTEM_NAME,
  description = "d4k Study Definitions Workbench. The Swiss Army Knife for DDF / USDM Study Definitions",
  version = VERSION
)

application_logger.info(f"Starting {SYSTEM_NAME}")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

authorisation = Auth0Service(app)
authorisation.register()

def protect_endpoint(request: Request) -> None:
  authorisation.protect_route(request, "/login")

def user_details(request: Request, db):
  user_info = request.session['userinfo']
  user, present_in_db = User.check(user_info['email'], db)
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
  if present_in_db:
    data = Study.list(1, 10, user.id, session)
    pagination = Pagination(data, "/index") 
    return templates.TemplateResponse("home/index.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})
  else:
    return templates.TemplateResponse("users/show.html", {'request': request, 'user': user})

@app.get("/users/{id}/show", dependencies=[Depends(protect_endpoint)])
def user_show(request: Request, id: int, session: Session = Depends(get_db)):
  user = User.find(id, session)
  return templates.TemplateResponse("users/show.html", {'request': request, 'user': user})

@app.post("/users/{id}/displayName", dependencies=[Depends(protect_endpoint)])
def user_display_name(request: Request, id: int, session: Session = Depends(get_db)):
  user = User.find(id, session)
  return templates.TemplateResponse(f"users/partials/displayName.html", {'request': request, 'user': user})

@app.get("/about", dependencies=[Depends(protect_endpoint)])
def about(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = {'release_notes': ReleaseNotes().notes(), 'system': SYSTEM_NAME, 'version': VERSION}
  return templates.TemplateResponse("about/about.html", {'request': request, 'user': user, 'data': data})

@app.get("/import/m11", dependencies=[Depends(protect_endpoint)])
def import_m11(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return templates.TemplateResponse("import/import_m11.html", {'request': request, 'user': user})

@app.get("/import/xl", dependencies=[Depends(protect_endpoint)])
def import_xl(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return templates.TemplateResponse("import/import_xl.html", {'request': request, 'user': user})

@app.post('/import/m11', dependencies=[Depends(protect_endpoint)])
async def import_m11(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_m11(request, background_tasks, templates, user, session)

@app.post('/import/xl', dependencies=[Depends(protect_endpoint)])
async def import_xl(request: Request, background_tasks: BackgroundTasks, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_xl(request, background_tasks, templates, user, session)

@app.get('/import/status', dependencies=[Depends(protect_endpoint)])
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = FileImport.list(page, size, user.id, session)
  pagination = Pagination(data, "/import/status") 
  return templates.TemplateResponse("import/status.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})

@app.get('/versions/{id}/summary', dependencies=[Depends(protect_endpoint)])
async def get_version_summary(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = usdm.study_version()
  #print(f"VERSION SUMMARY DATA: {data}")
  return templates.TemplateResponse("study_versions/summary.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/summary', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = {'id': version_id, 'study_design_id': study_design_id}
  return templates.TemplateResponse("study_designs/summary.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/overallParameters', dependencies=[Depends(protect_endpoint)])
async def get_study_design_o_parameters(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_overall_parameters(study_design_id)
  print(f"OVERALL SUMMARY DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/overall_parameters.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/designParameters', dependencies=[Depends(protect_endpoint)])
async def get_study_design_d_parameters(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_design_parameters(study_design_id)
  print(f"DESIGN PARAMETERS DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/design_parameters.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/schema', dependencies=[Depends(protect_endpoint)])
async def get_study_design_schema(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_schema(study_design_id)
  print(f"SCHEMA DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/schema.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/interventions', dependencies=[Depends(protect_endpoint)])
async def get_study_design_interventions(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_interventions(study_design_id)
  print(f"SCHEMA DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/section.html", {'request': request, 'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/estimands', dependencies=[Depends(protect_endpoint)])
async def get_vstudy_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_estimands(study_design_id)
  print(f"SCHEMA DATA: {data}")
  return templates.TemplateResponse("study_designs/partials/section.html", {'request': request, 'user': user, 'data': data})

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