from fastapi import Request
from fastapi.testclient import TestClient

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

def test_home(mocker):
  r, mt = mock_authorisation(mocker)
  client = mock_client()
  response = client.get("/")
  assert response.status_code == 200
  assert mock_called(r)
  assert mock_called(mt)

def mock_called(mock, count=1):
  return mock.call_count == count


