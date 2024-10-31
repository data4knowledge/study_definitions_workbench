import pytest
from app.main import app
from app.main import protect_endpoint
from app.model.user import User
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

def fake_user(mocker):
  check = mock_user_check(mocker)
  check.side_effect=[(factory_user(), True)]

def mock_user_check(mocker):
  return mocker.patch("app.model.user.User.check")

def mock_study_page(mocker):
  return mocker.patch("app.model.study.Study.page")

def mock_study_summary(mocker):
  return mocker.patch("app.model.study.Study.summary")

def factory_user() -> User:
  return User(**{'identifier': 'FRED', 'email': "fred@example.com", 'display_name': "Fred Smith", 'is_active': True, 'id': 1})
