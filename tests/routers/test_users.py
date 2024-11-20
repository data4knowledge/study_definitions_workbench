import pytest
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import *
from tests.mocks.fastapi_mocks import *

@pytest.fixture
def anyio_backend():
  return 'asyncio'

def test_user_show(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
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

def test_user_update_display_name(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
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
  
def test_user_update_display_name_error(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
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

def test_user_endpoint(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
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
