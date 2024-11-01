import pytest
import datetime
from app.main import app
from app.main import protect_endpoint
from app.model.user import User
from app.model.study import Study
from app.model.file_import import FileImport
from app.model.endpoint import Endpoint
from d4kms_ui.release_notes import ReleaseNotes
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

@pytest.fixture
def anyio_backend():
  return 'asyncio'

client = TestClient(app)
async_client =  AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

def test_home():
  response = client.get("/")
  assert response.status_code == 200
  result = response.text
  expected = """style="background-image: url('static/images/background.jpg'); height: 100vh">"""
  assert expected in result

@pytest.mark.anyio
async def test_login(mocker, monkeypatch):
  monkeypatch.setenv("SINGLE_USER", "True")
  response = await async_client.get("/login")
  assert response.status_code == 307
  assert str(response.next_request.url) == "http://test/index"

async def override_protect_endpoint(request: Request):
  request.session['userinfo'] = {'sub': "1234", 'email': 'user@example.com', 'nickname': 'Nickname'}
  return None

app.dependency_overrides[protect_endpoint] = override_protect_endpoint

def test_index_no_user(mocker):
  check = mock_user_check(mocker)
  check.side_effect=[(None, False)]
  response = client.get("/index")
  assert response.status_code == 200
  result = response.text
  expected = """Unable to determine user."""
  assert expected in result

def test_index_new_user(mocker):
  check = mock_user_check(mocker)
  check.side_effect=[(factory_user(), False)]
  response = client.get("/index")
  assert response.status_code == 200
  result = response.text
  expected = """Update Display Name"""
  assert expected in result

def test_index_existing_user_none(mocker):
  check = mock_user_check(mocker)
  check.side_effect=[(factory_user(), True)]
  page = mock_study_page(mocker)
  page.side_effect=[{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  response = client.get("/index")
  assert response.status_code == 200
  result = response.text
  expected = """You have not loaded any studies yet."""
  assert expected in result

def test_index_existing_user_studies(mocker):
  check = mock_user_check(mocker)
  check.side_effect=[(factory_user(), True)]
  page = mock_study_page(mocker)
  page.side_effect=[{'page': 1, 'size': 10, 'count': 1, 'filter': '', 'items': [{}]}]
  response = client.get("/index")
  assert response.status_code == 200
  result = response.text
  expected = """View Protocol"""
  assert expected in result

def test_study_select(mocker):
  fake_user(mocker)
  summary = mock_study_summary(mocker)
  summary.side_effect=["Study Summary"]
  response = client.patch(
    "/studies/15/select?action=select", 
    data={'list_studies': '1, 2'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  result = response.text
  expected = """<input type="hidden" name="list_studies" id="list_studies" value="1,2,15">"""
  assert expected in result

def test_study_deselect(mocker):
  fake_user(mocker)
  summary = mock_study_summary(mocker)
  summary.side_effect=["Study Summary"]
  response = client.patch(
    "/studies/15/select?action=deselect", 
    data={'list_studies': '1, 2,15'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  result = response.text
  expected = """<input type="hidden" name="list_studies" id="list_studies" value="1,2">"""
  assert expected in result

def test_study_delete(mocker):
  fake_user(mocker)
  sf = mock_study_find(mocker)
  sf.side_effect=[factory_study()]
  sfi = mock_study_file_imports(mocker)
  sfi.side_effect=[[[12,'1234-5678']]]
  fif = mock_file_import_find(mocker)
  fif.side_effect=[factory_file_import()]
  fid = mock_file_import_delete(mocker)
  fid.side_effect=[1]
  dfd = mock_data_file_delete(mocker)
  dfd.side_effect=[1]
  sd = mock_study_delete(mocker)
  sd.side_effect=[1]
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
  uf.side_effect=[factory_user()]
  uep = mock_user_endpoints_page(mocker)
  uep.side_effect=[{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  uv = mock_user_valid(mocker)
  uv.side_effect=[{'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}}]
  ev = mock_endpoint_valid(mocker)
  ev.side_effect=[{'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''},}]
  response = client.get("/users/1/show")
  assert response.status_code == 200
  result = response.text
  #print(f"RESULT: {result}")
  expected = """Enter a new display name"""
  assert expected in result

def test_user_update_display_name(mocker):
  uf = mock_user_find(mocker)
  uf.side_effect=[factory_user()]
  uudn = mock_user_update_display_name(mocker)
  uudn.side_effect=[(factory_user_2(), {'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}})]
  response = client.post(
    "/users/1/displayName",
    data={'name': 'Smithy'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  result = response.text
  #print(f"RESULT: {result}")
  expected = """Fred Smithy"""
  assert expected in result

def test_user_update_display_name_error(mocker):
  uf = mock_user_find(mocker)
  uf.side_effect=[factory_user()]
  uudn = mock_user_update_display_name(mocker)
  uudn.side_effect=[(None, {'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}})]
  response = client.post(
    "/users/1/displayName",
    data={'name': 'Smithy'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  result = response.text
  #print(f"RESULT: {result}")
  expected = """Fred Smith"""
  assert expected in result

def test_user_endpoint(mocker):
  uf = mock_user_find(mocker)
  uf.side_effect=[factory_user()]
  ec = mock_endpoint_create(mocker)
  ec.side_effect=[(factory_endpoint(),  {'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''}})]
  uep = mock_user_endpoints_page(mocker)
  uep.side_effects=[{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  response = client.post(
    "/users/1/endpoint",
    data={'name': 'Smithy', 'url': 'http://'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  result = response.text
  print(f"RESULT: {result}")
  expected = """Enter a name for the server"""
  assert expected in result

def fake_user(mocker):
  check = mock_user_check(mocker)
  check.side_effect=[(factory_user(), True)]

def mock_user_find(mocker):
  return mocker.patch("app.model.user.User.find")

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

def factory_release_notes() -> ReleaseNotes:
  rn = ReleaseNotes("dir")
  rn._text = "Release Notes"
  return rn