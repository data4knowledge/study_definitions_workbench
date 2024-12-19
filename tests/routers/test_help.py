import pytest
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import *
from tests.mocks.fastapi_mocks import *
from tests.mocks.utility_mocks import *
from tests.mocks.usdm_json_mocks import *
from tests.mocks.fhir_version_mocks import *

@pytest.fixture
def anyio_backend():
  return 'asyncio'

# Tests
def test_about(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  uc = mock_user_check_exists(mocker)
  mock_release_notes(mocker)
  response = client.get("/help/about")
  assert response.status_code == 200
  assert """Release Notes Test Testy""" in response.text
  assert mock_called(uc)

def test_examples(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  uc = mock_user_check_exists(mocker)
  mock_examples(mocker)
  response = client.get("/help/examples")
  assert response.status_code == 200
  assert """Examples Test Testy""" in response.text
  assert mock_called(uc)

def test_feedback(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  uc = mock_user_check_exists(mocker)
  mock_feedback(mocker)
  response = client.get("/help/examples")
  assert response.status_code == 200
  assert """Feedback Test Testy Testy""" in response.text
  assert mock_called(uc)

def test_user_guide(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  ug = mock_user_guide(mocker)
  response = client.get("/help/userGuide")
  assert response.status_code == 200
  assert mock_called(ug)

def test_user_guide_error(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  ug = mock_user_guide_error(mocker)
  response = client.get("/help/userGuide", follow_redirects=False)
  assert response.status_code == 200
  assert """Error downloading the user guide""" in response.text
  assert mock_called(ug)

def test_user_guide_splash(mocker, monkeypatch):
  client = mock_client(monkeypatch)
  ug = mock_user_guide(mocker)
  response = client.get("/help/userGuide/splash")
  assert response.status_code == 200
  assert mock_called(ug)

def test_user_guide_splash_error(mocker, monkeypatch):
  client = mock_client(monkeypatch)
  ug = mock_user_guide_error(mocker)
  response = client.get("/help/userGuide/splash", follow_redirects=False)
  assert response.status_code == 303
  assert mock_called(ug)

# Mocks
def mock_release_notes(mocker):
  rn = mocker.patch("d4kms_ui.ReleaseNotes.__init__")
  rn.side_effect = [None]
  rnn = mocker.patch("d4kms_ui.ReleaseNotes.notes")
  rnn.side_effect = ['Release Notes Test Testy']

def mock_examples(mocker):
  mp = mocker.patch("d4kms_ui.MarkdownPage.__init__")
  mp.side_effect = [None]
  mpr = mocker.patch("d4kms_ui.MarkdownPage.read")
  mpr.side_effect = ['Examples Test Testy']

def mock_feedback(mocker):
  mp = mocker.patch("d4kms_ui.MarkdownPage.__init__")
  mp.side_effect = [None]
  mpr = mocker.patch("d4kms_ui.MarkdownPage.read")
  mpr.side_effect = ['Feedback Test Testy Testy']

def mock_user_guide_error(mocker):
  mock = mocker.patch("app.routers.help._user_guide")
  mock.side_effect = [(None, None, None)]
  return mock

def mock_user_guide(mocker):
  mock = mocker.patch("app.routers.help._user_guide")
  mock.side_effect = [('tests/test_files/main/simple.txt', 'simple.txt', 'text/plain')]
  return mock

