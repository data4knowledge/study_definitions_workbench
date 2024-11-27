from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from fastapi import Request

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

def mock_client(monkeypatch):

  # Need this to stop exception of trying to send API call on elaborationpytes
  monkeypatch.setenv("SINGLE_USER", "True")
  from app.main import app
  
  return TestClient(app)

def mock_client_multiple(mocker):

  mock_authorisation(mocker)
  from app.main import app
  
  return TestClient(app)

def mock_async_client(monkeypatch):
  
  # Need this to stop exception of trying to send API call on elaborationpytes
  monkeypatch.setenv("SINGLE_USER", "True")
  from app.main import app
  
  return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")