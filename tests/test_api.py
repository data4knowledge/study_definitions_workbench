import pytest
from app.main import app
from app.main import protect_endpoint
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

def test_index(mocker):
  response = client.get("/index")
  assert response.status_code == 200
  result = response.text
  expected = """You have not loaded any studies yet."""
  assert expected in result

# def mock_protect_endpoint(mocker):
#   mock = mocker.patch("app.main.protect_endpoint")
#   mock.side_effect=[None]
