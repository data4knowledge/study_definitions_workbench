
from fastapi import Form, Depends, FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from d4kms_generic import application_logger
from d4kms_ui.pagination import Pagination
from app.database.database import get_db
from app.database.user import User
from app.database.version import Version
from app.database.file_import import FileImport
from app.database.endpoint import Endpoint
from app.database.user_endpoint import UserEndpoint
from app.model.connection_manager import connection_manager
from sqlalchemy.orm import Session
from app.utility.background import *
from app.utility.upload import *
from app.utility.template_methods import *
from app.model.usdm_json import USDMJson
from app.database.file_import import FileImport
from app import VERSION, SYSTEM_NAME
from app.dependencies.fhir_version import check_fhir_version
from app.utility.fhir_transmit import run_fhir_transmit
from app.database.database_manager import DatabaseManager as DBM
from app.model.exceptions import FindException
from app.model.file_handling.pfda_files import PFDAFiles
from app.model.file_handling.local_files import LocalFiles
from app.model.unified_diff.unified_diff import UnifiedDiff

from app.routers import transmissions, users, versions, help, studies, index, version_timelines
from app.dependencies.dependency import set_middleware_secret, protect_endpoint, authorisation
from app.dependencies.utility import user_details, admin_role_enabled
from app.dependencies.templates import templates

from app.configuration.configuration import application_configuration

DataFiles.clean_and_tidy()
DataFiles.check()
LocalFiles.check()
DBM.check()

app = FastAPI(
  title = SYSTEM_NAME,
  description = "d4k Study Definitions Workbench. The Swiss Army Knife for DDF / USDM Study Definitions",
  version = VERSION
)

application_logger.set_level(application_logger.DEBUG)
application_logger.info(f"Starting {SYSTEM_NAME}")

set_middleware_secret(app)
app.include_router(users.router)
app.include_router(transmissions.router)
app.include_router(versions.router)
app.include_router(version_timelines.router)
app.include_router(studies.router)
app.include_router(help.router)
app.include_router(index.router)
app.include_router(index.router)

@app.exception_handler(Exception)
async def exception_callback(request: Request, e: Exception):
  return templates.TemplateResponse(request, 'errors/error.html', {'user': None, 'data': {'error': f"An exception '{e}' was raised."}})

@app.exception_handler(FindException)
async def exception_callback(request: Request, e: FindException):
  return templates.TemplateResponse(request, 'errors/error.html', {'user': None, 'data': {'error': f"A find exception '{e}' was raised."}})

dir_path = os.path.dirname(os.path.realpath(__file__))
static_path = os.path.join(dir_path, "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")
application_logger.info(f"Static dir set to '{static_path}'")

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
  response = templates.TemplateResponse(request, 'home/home.html', {'data': {'version': VERSION}})
  return response

@app.get("/login")
async def login(request: Request):
  if application_configuration.single_user:
    return RedirectResponse("/index")
  else:
    if not 'id_token' in request.session:  # it could be userinfo instead of id_token
      return await authorisation.login(request, "callback")
    return RedirectResponse("/index")

@app.get("/fileList", dependencies=[Depends(protect_endpoint)])
def file_list(request: Request, dir: str, url: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  picker = application_configuration.file_picker
  valid, data, message = PFDAFiles().dir(dir) if picker['pfda'] else LocalFiles().dir(dir)
  data['url'] = url
  data['source'] = picker['source']
  if valid:
    return templates.TemplateResponse(request, "import/partials/other_file_list.html", {'user': user, 'data': data})
  else:
    application_logger.error(message)
    return templates.TemplateResponse(request, 'errors/partials/error.html', {'data': {'error': message}})

@app.get("/import/m11", dependencies=[Depends(protect_endpoint)])
def import_m11(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = application_configuration.file_picker
  data['dir'] = LocalFiles().root if data['os'] else ''
  data['required_ext'] = 'docx'
  data['other_files'] = False
  data['url'] = '/import/m11'
  return templates.TemplateResponse(request, "import/import_m11.html", {'user': user, 'data': data})

@app.get("/import/xl", dependencies=[Depends(protect_endpoint)])
def import_xl(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = application_configuration.file_picker
  data['dir'] = LocalFiles().root if data['os'] else ''
  data['required_ext'] = 'xlsx'
  data['other_files'] = True
  data['url'] = '/import/xl'
  return templates.TemplateResponse(request, "import/import_xl.html", {'user': user, 'data': data})

@app.get("/import/fhir", dependencies=[Depends(protect_endpoint)])
def import_fhir(request: Request, version: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  valid, description = check_fhir_version(version)
  if valid:
    data = application_configuration.file_picker
    data['version'] = version
    data['description'] = description
    data['dir'] = LocalFiles().root if data['os'] else ''
    data['required_ext'] = 'json'
    data['other_files'] = False
    data['url'] = '/import/fhir'
    return templates.TemplateResponse(request, "import/import_fhir.html", {'user': user, 'data': data})
  else:
    message = f"Invalid FHIR version '{version}'"
    application_logger.error(message)
    return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': message}})
    
@app.post('/import/m11', dependencies=[Depends(protect_endpoint)])
async def import_m11(request: Request, source: str='browser', session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_m11(request, templates, user, source)

@app.post('/import/xl', dependencies=[Depends(protect_endpoint)])
async def import_xl(request: Request, source: str='browser', session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_xl(request, templates, user, source)

@app.post('/import/fhir', dependencies=[Depends(protect_endpoint)])
async def import_fhir(request: Request, source: str='browser', session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  return await process_fhir(request, templates, user, source)

@app.get('/import/status', dependencies=[Depends(protect_endpoint)])
async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = {'page': page, 'size': size, 'filter': filter} 
  return templates.TemplateResponse(request, "import/status.html", {'user': user, 'data': data})

@app.get('/import/status/data', dependencies=[Depends(protect_endpoint)])
async def import_status_data(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = FileImport.page(page, size, user.id, session)
  pagination = Pagination(data, "/import/status/data") 
  return templates.TemplateResponse(request, "import/partials/status.html", {'user': user, 'pagination': pagination, 'data': data})

@app.get('/import/{id}/errors', dependencies=[Depends(protect_endpoint)])
async def import_errors(request: Request, id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  data = FileImport.find(id, session)
  files = DataFiles(data.uuid)
  fullpath, filename, exists = files.path('errors')
  if exists:
    return FileResponse(path=fullpath, filename=filename, media_type='text/plain')
  else:
    return templates.TemplateResponse(request, "errors/error.html", {'user': user, 'data': {'error': 'Something went wrong downloading the errors file for the import'}})

@app.get('/versions/{id}/usdm', dependencies=[Depends(protect_endpoint)])
async def get_version_usdm(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'version_id': id, 'json':  usdm._get_raw()}
  return templates.TemplateResponse(request, "study_versions/usdm.html", {'user': user, 'data': data})

@app.get('/versions/{id}/usdmDiff', dependencies=[Depends(protect_endpoint)])
async def get_version_usdm_diff(request: Request, id: int, previous: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  curr_usdm = USDMJson(id, session)
  prev_usdm = USDMJson(previous, session)
  curr_lines = curr_usdm._get_raw().split('\n')
  prev_lines = prev_usdm._get_raw().split('\n')
  diff = UnifiedDiff(prev_lines, curr_lines)
  data = {'version': curr_usdm.study_version(), 'version_id': id, 'diff': diff.to_html()}
  return templates.TemplateResponse(request, "study_versions/diff.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/summary', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
  return templates.TemplateResponse(request, "study_designs/summary.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/overallParameters', dependencies=[Depends(protect_endpoint)])
async def get_study_design_o_parameters(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_overall_parameters(study_design_id)
  #print(f"OVERALL SUMMARY DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/overall_parameters.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/designParameters', dependencies=[Depends(protect_endpoint)])
async def get_study_design_d_parameters(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_design_parameters(study_design_id)
  #print(f"DESIGN PARAMETERS DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/design_parameters.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/schema', dependencies=[Depends(protect_endpoint)])
async def get_study_design_schema(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_schema(study_design_id)
  #print(f"SCHEMA DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/schema.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/interventions', dependencies=[Depends(protect_endpoint)])
async def get_study_design_interventions(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_interventions(study_design_id)
  #print(f"INTERVENTION DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/interventions.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/estimands', dependencies=[Depends(protect_endpoint)])
async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.study_design_estimands(study_design_id)
  #print(f"ESTIMAND DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/estimands.html", {'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/timelines', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_timelines(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.timelines(study_design_id)
#   return templates.TemplateResponse(request, "study_designs/partials/timelines.html", {'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/soa', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_timeline_soa(request: Request, version_id: int, study_design_id: str, timeline_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.soa(study_design_id, timeline_id)
#   return templates.TemplateResponse(request, "timelines/soa.html", {'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/timelines/{timeline_id}/export/fhir_soa', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_timeline_soa(request: Request, version_id: int, study_design_id: str, timeline_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.soa(study_design_id, timeline_id)
#   print("EXPORT SOA")
#   return templates.TemplateResponse(request, "timelines/soa.html", {'user': user, 'data': data})

@app.get('/versions/{id}/safety', dependencies=[Depends(protect_endpoint)])
async def get_version_safety(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session)}
  #print(f"VERSION SUMMARY DATA: {data}")
  return templates.TemplateResponse(request, "study_versions/safety.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/safety', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
  return templates.TemplateResponse(request, "study_designs/safety.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/aeSpecialInterest', dependencies=[Depends(protect_endpoint)])
async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.adverse_events_special_interest(study_design_id)
  #print(f"AE SPECIAL INTEREST DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/ae_special_interest.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/safetyAssessments', dependencies=[Depends(protect_endpoint)])
async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.safety_assessments(study_design_id)
  #print(f"SAFETY ASSESSMENT DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/safety_assessments.html", {'user': user, 'data': data})

@app.get('/versions/{id}/statistics', dependencies=[Depends(protect_endpoint)])
async def get_version_statistics(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session)}
  #print(f"VERSION SUMMARY DATA: {data}")
  return templates.TemplateResponse(request, "study_versions/statistics.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/statistics', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
  return templates.TemplateResponse(request, "study_designs/statistics.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/sampleSize', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.sample_size(study_design_id)
  #print(f"SAMPLE SIZE DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/sample_size.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/analysisSets', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.analysis_sets(study_design_id)
  #print(f"ANALYSIS SETS DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/analysis_sets.html", {'user': user, 'data': data})

@app.get('/versions/{version_id}/studyDesigns/{study_design_id}/analysisObjective', dependencies=[Depends(protect_endpoint)])
async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(version_id, session)
  data = usdm.analysis_objectives(study_design_id)
  #print(f"ANALYSIS OBJECTIVES DATA: {data}")
  return templates.TemplateResponse(request, "study_designs/partials/analysis_objective.html", {'user': user, 'data': data})

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
      return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': f"The study with id '{id}' was not found."}})
  else:
    return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': f"Invalid FHIR M11 message version export requested. Version requested was '{version}'."}})

@app.get('/versions/{id}/transmit/{endpoint_id}', dependencies=[Depends(protect_endpoint)])
async def version_transmit(request: Request, id: int, endpoint_id: int, version: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  valid, description = check_fhir_version(version)
  if valid:
    run_fhir_transmit(id, endpoint_id, version, user)
    return RedirectResponse(f'/versions/{id}/summary')
  else:
    return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': f"Invalid FHIR M11 message version trsnsmission requested. Version requested was '{version}'."}})

@app.get('/versions/{id}/export/json', dependencies=[Depends(protect_endpoint)])
async def export_json(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  full_path, filename, media_type = usdm.json()
  if full_path:
    return FileResponse(path=full_path, filename=filename, media_type=media_type)
  else:
    return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': f"Error downloading the requested JSON file"}})

@app.get('/versions/{id}/export/protocol', dependencies=[Depends(protect_endpoint)])
async def export_protocol(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  full_path, filename, media_type = usdm.pdf()
  if full_path:
    return FileResponse(path=full_path, filename=filename, media_type=media_type)
  else:
    return templates.TemplateResponse(request, 'errors/error.html', {'user': user, 'data': {'error': f"Error downloading the requested PDF file"}})

@app.get("/versions/{id}/protocol", dependencies=[Depends(protect_endpoint)])
async def protocol(request: Request, id: int, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'version': usdm.study_version(), 'sections': usdm.protocol_sections(), 'section_list': usdm.protocol_sections_list()}
  #print(f"PROTOCOL SECTION: {data}")
  response = templates.TemplateResponse(request, 'versions/protocol/show.html', {"data": data, 'user': user})
  return response

@app.get("/versions/{id}/section/{section_id}", dependencies=[Depends(protect_endpoint)])
async def protocl_section(request: Request, id: int, section_id: str, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  usdm = USDMJson(id, session)
  data = {'section': usdm.section(section_id)}
  response = templates.TemplateResponse(request, 'versions/protocol//partials/section.html', {"data": data })
  return response

@app.get('/database/clean', dependencies=[Depends(protect_endpoint)])
async def database_clean(request: Request, session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  if admin_role_enabled(request):
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
  if admin_role_enabled(request):
    data = {}
    data['users'] = json.dumps(User.debug(session), indent=2)
    data['studies'] = json.dumps(Study.debug(session), indent=2)
    data['versions'] = json.dumps(Version.debug(session), indent=2)
    data['imports'] = json.dumps(FileImport.debug(session), indent=2)
    data['endpoints'] = json.dumps(Endpoint.debug(session), indent=2)
    data['user_endpoints'] = json.dumps(UserEndpoint.debug(session), indent=2)
    response = templates.TemplateResponse(request, 'database/debug.html', {'user': user, 'data': data})
    return response
  else:
    await connection_manager.error(f"Operation request denied", str(user.id))
    application_logger.error(f"User with id '{user.id}', email '{user.email}' attempted to debug the database!")
    return RedirectResponse(f"/users/{user.id}/show", status_code=status.HTTP_303_SEE_OTHER)

@app.patch("/debug", dependencies=[Depends(protect_endpoint)])
async def debug_level(request: Request, level: str='INFO', session: Session = Depends(get_db)):
  user, present_in_db = user_details(request, session)
  if admin_role_enabled(request) and level.upper() in ['DEBUG', 'INFO']:
    level = application_logger.DEBUG if level.upper() == 'DEBUG' else application_logger.INFO
    application_logger.set_level(level)
    return templates.TemplateResponse(request, 'users/partials/debug.html', {'user': user, 'data': {'debug': {'level': application_logger.get_level_str()}}})
  else:
    await connection_manager.error(f"Operation request denied", str(user.id))
    application_logger.error(f"User with id '{user.id}', email '{user.email}' attempted to change debug level!")
    return templates.TemplateResponse(request, 'users/partials/debug.html', {'user': user, 'data': {'debug': {'level': application_logger.get_level_str()}}})

@app.get("/logout")
def logout(request: Request):
  if application_configuration.multiple_user:
    url = authorisation.logout(request, "/")
    return RedirectResponse(url=url)
  else:
    return RedirectResponse("/")
  
@app.get("/callback")
async def callback(request: Request):
  try:
    await authorisation.save_token(request)
    return RedirectResponse("/index")
  except:
    return RedirectResponse("/logout")