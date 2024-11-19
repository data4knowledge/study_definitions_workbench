import pytest
from app.model.user import User
from app.model.file_import import FileImport
from app.model.endpoint import Endpoint
from fastapi import Request
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

@pytest.fixture
def anyio_backend():
  return 'asyncio'

def protect_endpoint():

  from app.main import app
  from app.main import protect_endpoint
  
  def override_protect_endpoint(request: Request):
    request.session['userinfo'] = {'sub': "1234", 'email': 'user@example.com', 'nickname': 'Nickname', 'roles': []}
    return None
  
  app.dependency_overrides[protect_endpoint] = override_protect_endpoint

def mock_authorisation(mocker):
  r = mocker.patch("d4kms_generic.auth0_service.Auth0Service.register")
  mt = mocker.patch("d4kms_generic.auth0_service.Auth0Service.management_token")
  r.side_effect = [[]]
  mt.side_effect = [[]]
  return r, mt

def mock_client():
  from app.main import app
  return TestClient(app)

def mock_async_client():
  from app.main import app
  return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

def test_user_show(mocker):
  r, mt = mock_authorisation(mocker)
  protect_endpoint()
  client = mock_client()
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
#  assert mock_called(r)
#  assert mock_called(mt)

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
#  r, mt = mock_authorisation(mocker)
  protect_endpoint()
  client = mock_client()
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
#  assert mock_called(r)
#  assert mock_called(mt)
  
def mock_user_update_display_name(mocker):
  mock = mocker.patch("app.model.user.User.update_display_name")
  mock.side_effect = [(factory_user_2(), {'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}})]
  return mock

def test_user_update_display_name_error(mocker):
#  r, mt = mock_authorisation(mocker)
  protect_endpoint()
  client = mock_client()
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
#  assert mock_called(r)
#  assert mock_called(mt)

def test_user_endpoint(mocker):
#  r, mt = mock_authorisation(mocker)
  protect_endpoint()
  client = mock_client()
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
#  assert mock_called(r)
#  assert mock_called(mt)

def mock_endpoint_create(mocker):
  mock = mocker.patch("app.model.endpoint.Endpoint.create")
  mock.side_effect = [(factory_endpoint(),  {'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''}})]
  return mock

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

def factory_user() -> User:
  return User(**{'identifier': 'FRED', 'email': "fred@example.com", 'display_name': "Fred Smith", 'is_active': True, 'id': 1})

def factory_user_2() -> User:
  return User(**{'identifier': 'FRED', 'email': "fred@example.com", 'display_name': "Fred Smithy", 'is_active': True, 'id': 1})

# def factory_study() -> Study:
#   return Study(**{'name': 'STUDYNAME', 'title': "Study Title", 'phase': "Phase 1", 'sponsor': 'ACME', 
#                  'sponsor_identifier': 'STUDY IDENTIFIER', 'nct_identifier': 'NCT12345678', 'id': 1, 'user_id': 1})

# def factory_version() -> Version:
#   return Version(**{'version': '1', 'id': 1, 'import_id': 1, 'study_id': 1})

# def factory_file_import() -> FileImport:
#   return FileImport(**{'filepath': 'filepath', 'filename': 'filename', 'type': "XXX", 'status': "Done", 'uuid': "1234-5678", 'id': 1, 'user_id': 1, 'created': datetime.datetime.now()})

def factory_endpoint() -> FileImport:
  return Endpoint(**{'name': 'Endpoint One', 'endpoint': 'http://example.com', 'type': "XXX", 'id': 1})

def mock_called(mock, count=1):
  return mock.call_count == count
