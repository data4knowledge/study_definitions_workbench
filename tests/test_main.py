import pytest
import datetime
from app.main import app
from app.main import protect_endpoint
from app.model.user import User
from app.model.study import Study
from app.model.version import Version
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
  sp = mock_study_page_none(mocker)
  response = client.get("/index")
  assert response.status_code == 200
  assert """You have not loaded any studies yet.""" in response.text
  assert mock_called(sp)

def mock_study_page_none(mocker):
  mock = mocker.patch("app.model.study.Study.page")
  mock.side_effect = [{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  return mock

def test_index_existing_user_studies(mocker):
  mock_user_check_exists(mocker)
  sp = mock_study_page(mocker)
  response = client.get("/index")
  assert response.status_code == 200
  assert """View Protocol""" in response.text
  assert """A study for Z""" in response.text
  assert mock_called(sp)

def mock_study_page(mocker):
  mock = mocker.patch("app.model.study.Study.page")
  items = [
    {'sponsor': 'ACME', 'sponsor_identifier': 'ACME', 'title': 'A study for X', 'versions': 1, 'phase': "Phase 1", 'import_type': "DOCX"},
    {'sponsor': 'Big Pharma', 'sponsor_identifier': 'BP', 'title': 'A study for Y', 'versions': 2, 'phase': "Phase 1", 'import_type': "XLSX"},
    {'sponsor': 'Big Pharma', 'sponsor_identifier': 'BP', 'title': 'A study for Z', 'versions': 3, 'phase': "Phase 4", 'import_type': "FHIR"}
  ]
  mock.side_effect = [{'page': 1, 'size': 10, 'count': 1, 'filter': '', 'items': items}]
  return mock

def test_study_select(mocker):
  mock_user_check_exists(mocker)
  ss = mock_study_summary(mocker)
  response = client.patch(
    "/studies/15/select?action=select", 
    data={'list_studies': '1, 2'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """<input type="hidden" name="list_studies" id="list_studies" value="1,2,15">""" in response.text
  assert mock_called(ss)

def mock_study_summary(mocker):
  mock = mocker.patch("app.model.study.Study.summary")
  mock.side_effect = ["Study Summary"]
  return mock

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
  #mock_user_check_exists(mocker)
  sf = mock_study_find(mocker)
  sfi = mock_study_file_imports(mocker)
  dfd = mock_data_file_delete(mocker)
  fif = mock_file_import_find(mocker)
  fid = mock_file_import_delete(mocker)
  sd = mock_study_delete(mocker)
  response = client.post(
    "/studies/delete", 
    data={'delete_studies': '1'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    follow_redirects=False
  )
  assert response.status_code == 303
  #assert response.status_code == 200
  assert str(response.next_request.url) == "http://testserver/index"
  assert mock_called(sf)
  #sf.assert_has_calls([mocker.call('1'), mocker.call('2'), mocker.call('15')])
  assert mock_called(sfi)
  #sfi.assert_has_calls([mocker.call('1'), mocker.call('2'), mocker.call('15')])
  assert mock_called(fif)
  assert mock_called(fid)
  assert mock_called(dfd)
  assert mock_called(sd)

def mock_study_file_imports(mocker):
  mock = mocker.patch("app.model.study.Study.file_imports")
  mock.side_effect = [[[12,'1234-5678']]]
  return mock

def mock_study_delete(mocker):
  mock = mocker.patch("app.model.study.Study.delete")
  mock.side_effect = [1]
  return mock

def mock_file_import_delete(mocker):
  mock = mocker.patch("app.model.file_import.FileImport.delete")
  mock.side_effect = [1]
  return mock

def mock_data_file_delete(mocker):
  mock = mocker.patch("app.model.file_handling.data_files.DataFiles.delete")
  mock.side_effect = [1]
  return mock

# @app.post("/studies/delete", dependencies=[Depends(protect_endpoint)])
# def study_delete(request: Request, delete_studies: Annotated[str, Form()]=None, session: Session = Depends(get_db)):
#   #user, present_in_db = user_details(request, session)
#   parts = delete_studies.split(',') if delete_studies else []
#   for id in parts:
#     study = Study.find(id, session)
#     imports = study.file_imports(session)
#     for im in imports:
#       files = DataFiles(im[1])
#       files.delete()
#       x = FileImport.find(im[0], session)
#       x.delete(session)
#     study.delete(session)
#   return RedirectResponse("/index", status_code=303)

def mock_study_find(mocker):
  mock = mocker.patch("app.model.study.Study.find")
  mock.side_effect = [factory_study()]
  return mock

def test_user_show(mocker):
  uf = mock_user_find(mocker)
  uep = mock_user_endpoints_page(mocker)
  uv = mock_user_valid(mocker)
  ev = mock_endpoint_valid(mocker)
  response = client.get("/users/1/show")
  assert response.status_code == 200
  assert """Enter a new display name""" in response.text
  assert mock_called(uf)
  assert mock_called(uv)
  assert mock_called(uep)
  assert mock_called(ev)

def mock_user_endpoints_page(mocker):
  mock = mocker.patch("app.model.user.User.endpoints_page")
  mock.side_effect = [{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  return mock

def mock_user_valid(mocker):
  mock = mocker.patch("app.model.user.User.valid")
  mock.side_effect = [{'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}}]
  return mock

def mock_endpoint_valid(mocker):
  mock = mocker.patch("app.model.endpoint.Endpoint.valid")
  mock.side_effect = [{'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''},}]
  return mock

def test_user_update_display_name(mocker):
  uf = mock_user_find(mocker)
  uudn = mock_user_update_display_name(mocker)
  response = client.post(
    "/users/1/displayName",
    data={'name': 'Smithy'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """Fred Smithy""" in response.text
  assert mock_called(uf)
  assert mock_called(uudn)

def mock_user_update_display_name(mocker):
  mock = mocker.patch("app.model.user.User.update_display_name")
  mock.side_effect = [(factory_user_2(), {'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}})]
  return mock

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
  assert mock_called(ec)

def mock_endpoint_create(mocker):
  mock = mocker.patch("app.model.endpoint.Endpoint.create")
  mock.side_effect = [(factory_endpoint(),  {'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''}})]
  return mock

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
  mock = mocker.patch("app.model.file_handling.local_files.LocalFiles.dir")
  files = []
  mock.side_effect = [(False, {'files': files, 'dir': 'xxx'}, 'Error Error Error!!!')]
  return mock

def error_logged(caplog, text):
  correct_level = caplog.records[-1].levelname == "ERROR"
  return text in caplog.records[-1].message and correct_level

def test_import_m11(mocker):
  uc = mock_user_check_exists(mocker)
  fp = mock_file_picker_os(mocker)
  response = client.get("/import/m11")
  assert response.status_code == 200
  assert '<h4 class="card-title">Import M11 Protocol</h4>' in response.text
  assert """<p>Select a single M11 file</p>""" in response.text
  assert mock_called(uc)
  assert mock_called(fp)

def test_import_xl(mocker):
  uc = mock_user_check_exists(mocker)
  fp = mock_file_picker_os(mocker)
  response = client.get("/import/xl")
  assert response.status_code == 200
  assert '<h4 class="card-title">Import USDM Excel Definition</h4>' in response.text
  assert '<p>Select a single Excel file and zero, one or more images files. </p>' in response.text
  assert mock_called(uc)
  assert mock_called(fp)

@pytest.mark.anyio
async def test_import_m11_execute(mocker):
  uc = mock_user_check_exists(mocker)
  pm11 = mock_process_m11(mocker)
  response = await async_client.post("/import/m11")
  assert response.status_code == 200
  assert '<h1>Fake M11 Response</h1>' in response.text
  assert mock_called(uc)
  assert mock_called(pm11)

def mock_process_m11(mocker):
  mock = mocker.patch("app.main.process_m11")
  mock.side_effect = ['<h1>Fake M11 Response</h1>']
  return mock

@pytest.mark.anyio
async def test_import_xl_execute(mocker):
  uc = mock_user_check_exists(mocker)
  pxl = mock_process_xl(mocker)
  response = await async_client.post("/import/xl")
  assert response.status_code == 200
  assert '<h1>Fake XL Response</h1>' in response.text
  assert mock_called(uc)
  assert mock_called(pxl)

def mock_process_xl(mocker):
  mock = mocker.patch("app.main.process_xl")
  mock.side_effect = ['<h1>Fake XL Response</h1>']
  return mock

def test_import_status(mocker):
  uc = mock_user_check_exists(mocker)
  response = client.get("/import/status?page=1&size=10&filter=")
  assert response.status_code == 200
  print(f"RESULT: {response.text}")
  assert '<h4 class="card-title">Import Status</h4>' in response.text
  assert mock_called(uc)

def test_import_status_data(mocker):
  uc = mock_user_check_exists(mocker)
  fip = mock_file_import_page(mocker)
  response = client.get("/import/status/data?page=1&size=10&filter=")
  assert response.status_code == 200
  assert '<div id="data_div">' in response.text
  assert '<th scope="col">Imported At</th>' in response.text
  assert mock_called(uc)
  assert mock_called(fip)

def mock_file_import_page(mocker):
  mock = mocker.patch("app.model.file_import.FileImport.page")
  mock.side_effect = [{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  return mock

def test_import_errors(mocker):
  uc = mock_user_check_exists(mocker)
  fif = mock_file_import_find(mocker)
  dfp = mock_data_file_path(mocker)
  response = client.get("/import/1/errors")
  assert response.status_code == 200
  assert 'Test File' in response.text
  assert mock_called(uc)
  assert mock_called(fif)
  assert mock_called(dfp)

def test_import_errors_error(mocker):
  uc = mock_user_check_exists(mocker)
  fif = mock_file_import_find(mocker)
  dfp = mock_data_file_path_error(mocker)
  response = client.get("/import/1/errors")
  assert response.status_code == 200
  assert '<p class="lead text-danger">Fatal Error</p>' in response.text
  assert '<p>Something went wrong downloading the errors file for the import</p>' in response.text
  assert mock_called(uc)
  assert mock_called(fif)
  assert mock_called(dfp)

def mock_file_import_find(mocker):
  mock = mocker.patch("app.model.file_import.FileImport.find")
  mock.side_effect = [factory_file_import()]
  return mock

def mock_data_file_path(mocker):
  mock = mocker.patch("app.model.file_handling.data_files.DataFiles.path")
  mock.side_effect = [('tests/test_files/a.txt', 'a.txt', True)]
  return mock

def mock_data_file_path_error(mocker):
  mock = mocker.patch("app.model.file_handling.data_files.DataFiles.path")
  mock.side_effect = [('', '', False)]
  return mock

def test_version_history(mocker):
  print(f"TEST")
  uc = mock_user_check_exists(mocker)
  usv = mock_usdm_study_version(mocker)
  uji = mock_usdm_json_init(mocker)
  response = client.get("/versions/1/history")
  assert response.status_code == 200
  assert '<h4 class="card-title">The Offical Study Title For Test</h4>' in response.text
  assert '<h6 class="card-subtitle mb-2 text-muted">Sponsor: Identifier For Test | Phase: Phase For Test | Identifier: </h6>' in response.text
  assert mock_called(uc)
  assert mock_called(usv)
  assert mock_called(uji)

def mock_usdm_study_version(mocker):
  mock = mocker.patch("app.model.usdm_json.USDMJson.study_version")
  mock.side_effect = [
    {
      'id': '1',
      'version_identifier': '1',
      'identifiers': {'Clinical Study Sponsor': 'Identifier For Test'},
      'titles': {'Official Study Title': 'The Offical Study Title For Test'},
      'study_designs': {'xxx': {'id': '2', 'name': 'design name', 'label': 'design label'}},
      'phase': {'standardCode': {'decode': 'Phase For Test'}}
    }
  ]
  return mock

def test_version_history_data(mocker):
  vf = mock_version_find(mocker)
  vp = mock_version_page(mocker)
  response = client.get("/versions/1/history/data?page=1&size=10&filter=")
  assert response.status_code == 200
  print(f"RESULT: {response.text}")
  assert '<th scope="col">Version</th>' in response.text
  assert '<td>1</td>' in response.text
  assert mock_called(vf)
  assert mock_called(vp)

def mock_version_find(mocker):
  mock = mocker.patch("app.model.version.Version.find")
  mock.side_effect = [factory_version()]
  return mock

def mock_version_page(mocker):
  mock = mocker.patch("app.model.version.Version.page")
  mock.side_effect = [{'page': 1, 'size': 10, 'count': 1, 'filter': '', 'items': [factory_version()]}]
  return mock

def mock_usdm_json_init(mocker):
  mock = mocker.patch("app.main.USDMJson.__init__")
  mock.side_effect = [None]
  return mock

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

def mock_release_notes(mocker):
  rn = mocker.patch("d4kms_ui.ReleaseNotes.__init__")
  rn.side_effect = [None]
  rnn = mocker.patch("d4kms_ui.ReleaseNotes.notes")
  rnn.side_effect = ['Release Notes Test Testy']

def factory_user() -> User:
  return User(**{'identifier': 'FRED', 'email': "fred@example.com", 'display_name': "Fred Smith", 'is_active': True, 'id': 1})

def factory_user_2() -> User:
  return User(**{'identifier': 'FRED', 'email': "fred@example.com", 'display_name': "Fred Smithy", 'is_active': True, 'id': 1})

def factory_study() -> Study:
  return Study(**{'name': 'STUDYNAME', 'title': "Study Title", 'phase': "Phase 1", 'sponsor': 'ACME', 
                 'sponsor_identifier': 'STUDY IDENTIFIER', 'nct_identifier': 'NCT12345678', 'id': 1, 'user_id': 1})

def factory_version() -> Version:
  return Version(**{'version': '1', 'id': 1, 'import_id': 1, 'study_id': 1})

def factory_file_import() -> FileImport:
  return FileImport(**{'filepath': 'filepath', 'filename': 'filename', 'type': "XXX", 'status': "Done", 'uuid': "1234-5678", 'id': 1, 'user_id': 1, 'created': datetime.datetime.now()})

def factory_endpoint() -> FileImport:
  return Endpoint(**{'name': 'Endpoint One', 'endpoint': 'http://example.com', 'type': "XXX", 'id': 1})