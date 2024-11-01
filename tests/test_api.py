import pytest
import datetime
from app.main import app
from app.main import protect_endpoint
from app.model.user import User
from app.model.study import Study
from app.model.file_import import FileImport
from app.model.endpoint import Endpoint
from app.utility.environment import file_picker
from d4kms_ui.release_notes import ReleaseNotes
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

@pytest.fixture
def anyio_backend():
  return 'asyncio'

client = TestClient(app)
async_client =  AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

async def override_protect_endpoint(request: Request):
  request.session['userinfo'] = {'sub': "1234", 'email': 'user@example.com', 'nickname': 'Nickname'}
  return None

app.dependency_overrides[protect_endpoint] = override_protect_endpoint

def test_home():
  response = client.get("/")
  assert response.status_code == 200
  assert """style="background-image: url('static/images/background.jpg'); height: 100vh">""" in response.text in response.text

@pytest.mark.anyio
async def test_login(mocker, monkeypatch):
  monkeypatch.setenv("SINGLE_USER", "True")
  response = await async_client.get("/login")
  assert response.status_code == 307
  assert str(response.next_request.url) == "http://test/index"

def test_index_no_user(mocker):
  mock_user_check_fail(mocker)
  response = client.get("/index")
  assert response.status_code == 200
  assert """Unable to determine user.""" in response.text

def test_index_new_user(mocker):
  mock_user_check_new(mocker)
  response = client.get("/index")
  assert response.status_code == 200
  assert """Update Display Name""" in response.text

def test_index_existing_user_none(mocker):
  mock_user_check_exists(mocker)
  page = mock_study_page(mocker)
  page.side_effect = [{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  response = client.get("/index")
  assert response.status_code == 200
  assert """You have not loaded any studies yet.""" in response.text

def test_index_existing_user_studies(mocker):
  mock_user_check_exists(mocker)
  page = mock_study_page(mocker)
  page.side_effect = [{'page': 1, 'size': 10, 'count': 1, 'filter': '', 'items': [{}]}]
  response = client.get("/index")
  assert response.status_code == 200
  assert """View Protocol""" in response.text

def test_study_select(mocker):
  mock_user_check_exists(mocker)
  summary = mock_study_summary(mocker)
  summary.side_effect = ["Study Summary"]
  response = client.patch(
    "/studies/15/select?action=select", 
    data={'list_studies': '1, 2'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """<input type="hidden" name="list_studies" id="list_studies" value="1,2,15">""" in response.text

def test_study_deselect(mocker):
  mock_user_check_exists(mocker)
  summary = mock_study_summary(mocker)
  summary.side_effect = ["Study Summary"]
  response = client.patch(
    "/studies/15/select?action=deselect", 
    data={'list_studies': '1, 2,15'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """<input type="hidden" name="list_studies" id="list_studies" value="1,2">""" in response.text

def test_study_delete(mocker):
  mock_user_check_exists(mocker)
  sf = mock_study_find(mocker)
  sf.side_effect = [factory_study()]
  sfi = mock_study_file_imports(mocker)
  sfi.side_effect = [[[12,'1234-5678']]]
  fif = mock_file_import_find(mocker)
  fif.side_effect = [factory_file_import()]
  fid = mock_file_import_delete(mocker)
  fid.side_effect = [1]
  dfd = mock_data_file_delete(mocker)
  dfd.side_effect = [1]
  sd = mock_study_delete(mocker)
  sd.side_effect = [1]
  response = client.post(
    "/studies/delete", 
    data={'delete_studies': '1'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  #assert sf.call_count == 3
  #sf.assert_has_calls([mocker.call('1'), mocker.call('2'), mocker.call('15')])
  #assert sfi.call_count == 3
  #sfi.assert_has_calls([mocker.call('1'), mocker.call('2'), mocker.call('15')])
  assert response.status_code == 307
  assert str(response.next_request.url) == "http://test/index"

def test_user_show(mocker):
  uf = mock_user_find(mocker)
  uep = mock_user_endpoints_page(mocker)
  uep.side_effect = [{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  uv = mock_user_valid(mocker)
  uv.side_effect = [{'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}}]
  ev = mock_endpoint_valid(mocker)
  ev.side_effect = [{'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''},}]
  response = client.get("/users/1/show")
  assert response.status_code == 200
  assert """Enter a new display name""" in response.text
  assert mock_called(uf)

def test_user_update_display_name(mocker):
  uf = mock_user_find(mocker)
  uudn = mock_user_update_display_name(mocker)
  uudn.side_effect = [(factory_user_2(), {'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}})]
  response = client.post(
    "/users/1/displayName",
    data={'name': 'Smithy'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """Fred Smithy""" in response.text
  assert mock_called(uf)

def test_user_update_display_name_error(mocker):
  uf = mock_user_find(mocker)
  uudn = mock_user_update_display_name(mocker)
  uudn.side_effect = [(None, {'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}})]
  response = client.post(
    "/users/1/displayName",
    data={'name': 'Smithy'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """Fred Smith""" in response.text
  assert mock_called(uf)

def test_user_endpoint(mocker):
  uf = mock_user_find(mocker)
  ec = mock_endpoint_create(mocker)
  ec.side_effect = [(factory_endpoint(),  {'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''}})]
  uep = mock_user_endpoints_page(mocker)
  uep.side_effects=[{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  response = client.post(
    "/users/1/endpoint",
    data={'name': 'Smithy', 'url': 'http://'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """Enter a name for the server""" in response.text
  assert mock_called(uf)

def test_about(mocker):
  uc = mock_user_check_exists(mocker)
  mock_release_notes(mocker)
  response = client.get("/about")
  assert response.status_code == 200
  assert """Release Notes Test Testy""" in response.text
  assert mock_called(uc)

def test_file_list_local(mocker):
  uc = mock_user_check_exists(mocker)
  fp = mock_file_picker_os(mocker)
  lfd = mock_local_files_dir(mocker)
  response = client.get("/fileList?dir=xxx&url=http://example.com")
  assert response.status_code == 200
  #print(f"RESULT: {response.text}")
  assert """<p class="card-text">a-file.txt</p>""" in response.text
  assert """<p class="card-text">100 kb</p>""" in response.text
  assert mock_called(uc)
  assert mock_called(fp)
  assert mock_called(lfd)

def test_file_list_local_invalid(mocker, caplog):
  uc = mock_user_check_exists(mocker)
  fp = mock_file_picker_os(mocker)
  lfd = mock_local_files_dir_error(mocker)
  response = client.get("/fileList?dir=xxx&url=http://example.com")
  assert response.status_code == 200
  print(f"RESULT: {response.text}")
  assert """Error Error Error!!!""" in response.text
  assert mock_called(uc)
  assert mock_called(fp)
  assert mock_called(lfd)
  assert error_logged(caplog, "Error Error Error!!!")

def mock_file_picker_os(mocker):
  fp = mocker.patch("app.main.file_picker")
  fp.side_effect = [{'browser': False, 'os': True, 'pfda': False, 'source': 'os'}]
  return fp

def mock_called(mock, count=1):
  return mock.call_count == count

def mock_local_files_dir(mocker):
  lfd = mocker.patch("app.model.file_handling.local_files.LocalFiles.dir")
  ts = datetime.datetime.now()
  files = [{'uid': 1234-5678, 'type': 'File', 'name': 'a-file.txt', 'path': 'xxx/a-file.txt', 'created_at': ts, 'file_size': '100 kb'}]
  lfd.side_effect = [(True, {'files': files, 'dir': 'xxx'}, '')]
  return lfd

def mock_local_files_dir_error(mocker):
  lfd = mocker.patch("app.model.file_handling.local_files.LocalFiles.dir")
  files = []
  lfd.side_effect = [(False, {'files': files, 'dir': 'xxx'}, 'Error Error Error!!!')]
  return lfd

def error_logged(caplog, text):
    correct_level = caplog.records[-1].levelname == "ERROR"
    return text in caplog.records[-1].message and correct_level
    
# @app.get("/import/m11", dependencies=[Depends(protect_endpoint)])
# def import_m11(request: Request, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   data = file_picker()
#   data['dir'] = LocalFiles().root if data['os'] else ''
#   data['required_ext'] = 'docx'
#   data['other_files'] = False
#   data['url'] = '/import/m11'
#   return templates.TemplateResponse("import/import_m11.html", {'request': request, 'user': user, 'data': data})

# @app.get("/import/xl", dependencies=[Depends(protect_endpoint)])
# def import_xl(request: Request, session: Session = Depends(get_db)):
#   print(f"IMPORT: XL")
#   user, present_in_db = user_details(request, session)
#   data = file_picker()
#   data['dir'] = LocalFiles().root if data['os'] else ''
#   data['required_ext'] = 'xlsx'
#   data['other_files'] = True
#   data['url'] = '/import/xl'
#   return templates.TemplateResponse("import/import_xl.html", {'request': request, 'user': user, 'data': data})

# @app.post('/import/m11', dependencies=[Depends(protect_endpoint)])
# async def import_m11(request: Request, source: str='browser', session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   return await process_m11(request, templates, user, source)

# @app.post('/import/xl', dependencies=[Depends(protect_endpoint)])
# async def import_xl(request: Request, source: str='browser', session: Session = Depends(get_db)):
#   print(f"IMPORT: XL")
#   user, present_in_db = user_details(request, session)
#   return await process_xl(request, templates, user, source)

# @app.get('/import/status', dependencies=[Depends(protect_endpoint)])
# async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   data = {'page': page, 'size': size, 'filter': filter} 
#   return templates.TemplateResponse("import/status.html", {'request': request, 'user': user, 'data': data})

# @app.get('/import/status/data', dependencies=[Depends(protect_endpoint)])
# async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   data = FileImport.page(page, size, user.id, session)
#   pagination = Pagination(data, "/import/status/data") 
#   return templates.TemplateResponse("import/partials/status.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})

# @app.get('/import/{id}/errors', dependencies=[Depends(protect_endpoint)])
# async def import_status(request: Request, id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   data = FileImport.find(id, session)
#   files = DataFiles(data.uuid)
#   fullpath, filename, exists = files.path('errors')
#   if exists:
#     return FileResponse(path=fullpath, filename=filename, media_type='text/plain')
#   else:
#     return templates.TemplateResponse("errors/error.html", {'request': request, 'user': user, 'data': {'error': 'Something went wrong downloading the errors file for the import'}})

# @app.get('/versions/{id}/summary', dependencies=[Depends(protect_endpoint)])
# async def get_version_summary(request: Request, id: int, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(id, session)
#   data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session)}
#   #print(f"VERSION SUMMARY DATA: {data}")
#   return templates.TemplateResponse("study_versions/summary.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/summary', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
#   return templates.TemplateResponse("study_designs/summary.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/overallParameters', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_o_parameters(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.study_design_overall_parameters(study_design_id)
#   #print(f"OVERALL SUMMARY DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/overall_parameters.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/designParameters', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_d_parameters(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.study_design_design_parameters(study_design_id)
#   #print(f"DESIGN PARAMETERS DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/design_parameters.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/schema', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_schema(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.study_design_schema(study_design_id)
#   #print(f"SCHEMA DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/schema.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/interventions', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_interventions(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.study_design_interventions(study_design_id)
#   #print(f"INTERVENTION DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/interventions.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/estimands', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.study_design_estimands(study_design_id)
#   #print(f"ESTIMAND DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/estimands.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{id}/safety', dependencies=[Depends(protect_endpoint)])
# async def get_version_safety(request: Request, id: int, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(id, session)
#   data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session)}
#   #print(f"VERSION SUMMARY DATA: {data}")
#   return templates.TemplateResponse("study_versions/safety.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/safety', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
#   return templates.TemplateResponse("study_designs/safety.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/aeSpecialInterest', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.adverse_events_special_interest(study_design_id)
#   #print(f"AE SPECIAL INTEREST DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/ae_special_interest.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/safetyAssessments', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_estimands(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.safety_assessments(study_design_id)
#   #print(f"SAFETY ASSESSMENT DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/safety_assessments.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{id}/statistics', dependencies=[Depends(protect_endpoint)])
# async def get_version_statistics(request: Request, id: int, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(id, session)
#   data = {'version': usdm.study_version(), 'endpoints': User.endpoints_page(1, 100, user.id, session)}
#   #print(f"VERSION SUMMARY DATA: {data}")
#   return templates.TemplateResponse("study_versions/statistics.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/statistics', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = {'id': version_id, 'study_design_id': study_design_id, 'm11': usdm.m11}
#   return templates.TemplateResponse("study_designs/statistics.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/sampleSize', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.sample_size(study_design_id)
#   #print(f"SAMPLE SIZE DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/sample_size.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/analysisSets', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.analysis_sets(study_design_id)
#   #print(f"ANALYSIS SETS DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/analysis_sets.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{version_id}/studyDesigns/{study_design_id}/analysisObjective', dependencies=[Depends(protect_endpoint)])
# async def get_study_design_summary(request: Request, version_id: int, study_design_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(version_id, session)
#   data = usdm.analysis_objectives(study_design_id)
#   #print(f"ANALYSIS OBJECTIVES DATA: {data}")
#   return templates.TemplateResponse("study_designs/partials/analysis_objective.html", {'request': request, 'user': user, 'data': data})

# @app.get('/versions/{id}/export/json', dependencies=[Depends(protect_endpoint)])
# async def export_json(request: Request, id: int, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(id, session)
#   full_path, filename, media_type = usdm.json()
#   if full_path:
#     return FileResponse(path=full_path, filename=filename, media_type=media_type)
#   else:
#     return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"Error downloading the requested JSON file"}})

# @app.get('/versions/{id}/export/protocol', dependencies=[Depends(protect_endpoint)])
# async def export_protocol(request: Request, id: int, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(id, session)
#   full_path, filename, media_type = usdm.pdf()
#   if full_path:
#     return FileResponse(path=full_path, filename=filename, media_type=media_type)
#   else:
#     return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"Error downloading the requested PDF file"}})

# @app.get("/versions/{id}/protocol", dependencies=[Depends(protect_endpoint)])
# async def protocol(request: Request, id: int, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(id, session)
#   data = {'version': usdm.study_version(), 'sections': usdm.protocol_sections(), 'section_list': usdm.protocol_sections_list()}
#   #print(f"PROTOCOL SECTION: {data}")
#   response = templates.TemplateResponse('versions/protocol/show.html', {"request": request, "data": data, 'user': user})
#   return response

# @app.get("/versions/{id}/section/{section_id}", dependencies=[Depends(protect_endpoint)])
# async def protocl_section(request: Request, id: int, section_id: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(id, session)
#   data = {'section': usdm.section(section_id)}
#   response = templates.TemplateResponse('versions/protocol//partials/section.html', {"request": request, "data": data })
#   return response




# **************************************************** On Hold ***************************************************

# @app.get("/import/fhir", dependencies=[Depends(protect_endpoint)])
# def import_fhir(request: Request, version: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   valid, description = check_fhir_version(version)
#   if valid:
#     data = file_picker()
#     data['version'] = version
#     data['description'] = description
#     data['dir'] = LocalFiles().root if data['os'] else ''
#     data['required_ext'] = 'json'
#     data['other_files'] = False
#     data['url'] = '/import/fhir'
#     return templates.TemplateResponse("import/import_fhir.html", {'request': request, 'user': user, 'data': data})
#   else:
#     message = f"Invalid FHIR version '{version}'"
#     application_logger.error(message)
#     return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': message}})
    
# @app.post('/import/fhir', dependencies=[Depends(protect_endpoint)])
# async def import_fhir(request: Request, source: str='browser', session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   return await process_fhir(request, templates, user, source)

# @app.get('/transmissions/status', dependencies=[Depends(protect_endpoint)])
# async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   # data = Transmission.page(page, size, user.id, session)
#   # pagination = Pagination(data, "/transmissions/status")
#   data = {'page': page, 'size': size, 'filter': filter} 
#   return templates.TemplateResponse("transmissions/status.html", {'request': request, 'user': user, 'data': data})

# @app.get('/transmissions/status/data', dependencies=[Depends(protect_endpoint)])
# async def import_status(request: Request, page: int, size: int, filter: str="", session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   data = Transmission.page(page, size, user.id, session)
#   pagination = Pagination(data, "/transmissions/status/data")
#   return templates.TemplateResponse("transmissions/partials/status.html", {'request': request, 'user': user, 'pagination': pagination, 'data': data})

# @app.get('/versions/{id}/export/fhir', dependencies=[Depends(protect_endpoint)])
# async def export_fhir(request: Request, id: int, version: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   usdm = USDMJson(id, session)
#   valid, description = check_fhir_version(version)
#   if valid:
#     full_path, filename, media_type = usdm.fhir(version.upper())
#     if full_path:
#       return FileResponse(path=full_path, filename=filename, media_type=media_type)
#     else:
#       return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"The study with id '{id}' was not found."}})
#   else:
#     return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"Invalid FHIR M11 message version export requested. Version requested was '{version}'."}})

# @app.get('/versions/{id}/transmit/{endpoint_id}', dependencies=[Depends(protect_endpoint)])
# async def version_transmit(request: Request, id: int, endpoint_id: int, version: str, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   valid, description = check_fhir_version(version)
#   if valid:
#     run_fhir_transmit(id, endpoint_id, version, user)
#     return RedirectResponse(f'/versions/{id}/summary')
#   else:
#     return templates.TemplateResponse('errors/error.html', {"request": request, 'user': user, 'data': {'error': f"Invalid FHIR M11 message version trsnsmission requested. Version requested was '{version}'."}})


# @app.get('/database/clean', dependencies=[Depends(protect_endpoint)])
# async def database_clean(request: Request, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   if user.email == "daveih1664dk@gmail.com":
#     database_managr = DBM(session)
#     database_managr.clear_all()
#     endpoint, validation = Endpoint.create('LOCAL TEST', 'http://localhost:8010/m11', "FHIR", user.id, session)
#     endpoint, validation = Endpoint.create('Hugh Server', 'https://fs-01.azurewebsites.net', "FHIR", user.id, session)
#     endpoint, validation = Endpoint.create('HAPI Server', 'https://hapi.fhir.org/baseR5', "FHIR", user.id, session)
#     application_logger.info(f"User '{user.id}', '{user.email} cleared the database")
#   else:
#     # Error here
#     application_logger.warning(f"User '{user.id}', '{user.email} attempted to clear the database!")
#   return RedirectResponse("/index")

# @app.get("/database/debug", dependencies=[Depends(protect_endpoint)])
# async def database_clean(request: Request, session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   if user.email == "daveih1664dk@gmail.com":
#     data = {}
#     data['users'] = json.dumps(User.debug(session), indent=2)
#     data['studies'] = json.dumps(Study.debug(session), indent=2)
#     data['versions'] = json.dumps(Version.debug(session), indent=2)
#     data['imports'] = json.dumps(FileImport.debug(session), indent=2)
#     data['endpoints'] = json.dumps(Endpoint.debug(session), indent=2)
#     data['user_endpoints'] = json.dumps(UserEndpoint.debug(session), indent=2)
#     response = templates.TemplateResponse('database/debug.html', {'request': request, 'user': user, 'data': data})
#     return response
#   else:
#     await connection_manager.error(f"Operation request denied", str(user.id))
#     application_logger.error(f"User '{user.id}', '{user.email} attempted to debug the database!")
#     return RedirectResponse(f"/users/{user.id}/show", status_code=303)

# @app.patch("/debug", dependencies=[Depends(protect_endpoint)])
# async def debug_level(request: Request, level: str='INFO', session: Session = Depends(get_db)):
#   user, present_in_db = user_details(request, session)
#   if user.email == "daveih1664dk@gmail.com" and level.upper() in ['DEBUG', 'INFO']:
#     level = application_logger.DEBUG if level.upper() == 'DEBUG' else application_logger.INFO
#     application_logger.set_level(level)
#     return templates.TemplateResponse('users/partials/debug.html', {'request': request, 'user': user, 'data': {'debug': {'level': application_logger.get_level_str()}}})
#   else:
#     await connection_manager.error(f"Operation request denied", str(user.id))
#     application_logger.error(f"User '{user.id}', '{user.email} attempted to change debug level!")
#     return templates.TemplateResponse('users/partials/debug.html', {'request': request, 'user': user, 'data': {'debug': {'level': application_logger.get_level_str()}}})

# @app.get("/logout")
# def logout(request: Request):
#   url = authorisation.logout(request, "home")
#   return RedirectResponse(url=url)

# @app.get("/callback")
# async def callback(request: Request):
#   try:
#     await authorisation.save_token(request)
#     return RedirectResponse("/index")
#   except:
#     return RedirectResponse("/logout")

def mock_user_check_exists(mocker):
  uc = mock_user_check(mocker)
  uc.side_effect = [(factory_user(), True)]
  return uc

def mock_user_check_new(mocker):
  uc = mock_user_check(mocker)
  uc.side_effect = [(factory_user(), False)]
  return uc

def mock_user_check_fail(mocker):
  uc = mock_user_check(mocker)
  uc.side_effect = [(None, False)]
  return uc

def mock_user_find(mocker):
  uf = mocker.patch("app.model.user.User.find")
  uf.side_effect = [factory_user()]
  return uf

def mock_user_check(mocker):
  return mocker.patch("app.model.user.User.check")

def mock_user_endpoints_page(mocker):
  return mocker.patch("app.model.user.User.endpoints_page")

def mock_user_valid(mocker):
  return mocker.patch("app.model.user.User.valid")

def mock_user_update_display_name(mocker):
  return mocker.patch("app.model.user.User.update_display_name")

def mock_endpoint_create(mocker):
  return mocker.patch("app.model.endpoint.Endpoint.create")

def mock_endpoint_valid(mocker):
  return mocker.patch("app.model.endpoint.Endpoint.valid")

def mock_study_find(mocker):
  return mocker.patch("app.model.study.Study.find")

def mock_study_file_imports(mocker):
  return mocker.patch("app.model.study.Study.file_imports")

def mock_study_page(mocker):
  return mocker.patch("app.model.study.Study.page")

def mock_study_summary(mocker):
  return mocker.patch("app.model.study.Study.summary")

def mock_study_delete(mocker):
  return mocker.patch("app.model.study.Study.delete")

def mock_delete(mocker):
  return mocker.patch("app.model.data_files.DataFiles.delete")

def mock_file_import_find(mocker):
  return mocker.patch("app.model.file_import.FileImport.find")

def mock_file_import_delete(mocker):
  return mocker.patch("app.model.file_import.FileImport.delete")

def mock_data_file_delete(mocker):
  return mocker.patch("app.model.file_handling.data_files.DataFiles.delete")

def factory_user() -> User:
  return User(**{'identifier': 'FRED', 'email': "fred@example.com", 'display_name': "Fred Smith", 'is_active': True, 'id': 1})

def factory_user_2() -> User:
  return User(**{'identifier': 'FRED', 'email': "fred@example.com", 'display_name': "Fred Smithy", 'is_active': True, 'id': 1})

def factory_study() -> Study:
  return Study(**{'name': 'STUDYNAME', 'title': "Study Title", 'phase': "Phase 1", 'sponsor': 'ACME', 
                 'sponsor_identifier': 'STUDY IDENTIFIER', 'nct_identifier': 'NCT12345678', 'id': 1, 'user_id': 1})

def factory_file_import() -> FileImport:
  return FileImport(**{'filepath': 'filepath', 'filename': 'filename', 'type': "XXX", 'status': "Done", 'uuid': "1234-5678", 'id': 1, 'user_id': 1, 'created': datetime.datetime.now()})

def factory_endpoint() -> FileImport:
  return Endpoint(**{'name': 'Endpoint One', 'endpoint': 'http://example.com', 'type': "XXX", 'id': 1})

def mock_release_notes(mocker):
  rn = mocker.patch("d4kms_ui.ReleaseNotes.__init__")
  rn.side_effect = [None]
  rnn = mocker.patch("d4kms_ui.ReleaseNotes.notes")
  rnn.side_effect = ['Release Notes Test Testy']
