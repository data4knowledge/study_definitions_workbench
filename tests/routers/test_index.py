import pytest
from tests.mocks.general_mocks import mock_called, mock_parameters_correct
from tests.mocks.user_mocks import *
from tests.mocks.fastapi_mocks import *
from tests.mocks.utility_mocks import *
from tests.mocks.usdm_json_mocks import *
from tests.mocks.fhir_version_mocks import *
from sqlalchemy.orm import Session

@pytest.fixture
def anyio_backend():
  return 'asyncio'

# Tests
def test_index_no_user(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_fail(mocker)
  response = client.get("/index")
  assert response.status_code == 200
  assert """Unable to determine user.""" in response.text

def test_index_new_user(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_new(mocker)
  response = client.get("/index")
  assert response.status_code == 200
  assert """Loading...""" in response.text

def test_index_existing_user_none(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_exists(mocker)
  response = client.get("/index")
  assert response.status_code == 200
  assert """Loading...""" in response.text

def test_index_existing_user_studies(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_exists(mocker)
  response = client.get("/index")
  assert response.status_code == 200
  assert """Loading...""" in response.text

def test_index_page_none(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_exists(mocker)
  sp = mock_study_page_none(mocker)
  response = client.get("/index/page?page=1&size=5")
  assert response.status_code == 200
  assert """You have not loaded any studies yet.""" in response.text
  assert mock_called(sp)
  assert sp.mock_calls[0].args[0] == 1
  assert sp.mock_calls[0].args[1] == 5
  assert sp.mock_calls[0].args[2] == 1

def test_index_page(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_exists(mocker)
  sp = mock_study_page(mocker)
  response = client.get("/index/page?page=2&size=10")
  assert response.status_code == 200
  assert """View Protocol""" in response.text
  assert """A study for Z""" in response.text
  assert mock_called(sp)
  assert sp.mock_calls[0].args[0] == 2
  assert sp.mock_calls[0].args[1] == 10
  assert sp.mock_calls[0].args[2] == 1

def test_index_pagination(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_exists(mocker)
  sp = mock_study_page_many(mocker)
  response = client.get("/index/page?page=1&size=12")
  #print(f"RESPONSE: {response.text}")
  assert response.status_code == 200
  assert """View Protocol""" in response.text
  assert """A study for X""" in response.text
  assert """<a class="dropdown-item" href="#" hx-get="/index/page?page=1&amp;size=96&amp;filter=" hx-trigger="click" hx-target="#data_div" hx-swap="outerHTML">96</a>""" in response.text
  assert """<button class="btn btn-sm btn-outline-primary rounded-5 mb-1  " href="#" hx-get="/index/page?page=4&amp;size=12&amp;filter=" hx-trigger="click" hx-target="#data_div" hx-swap="outerHTML">4</a>""" in response.text
  assert """<button class="btn btn-sm btn-outline-primary rounded-5 mb-1  disabled" href="#" hx-get="" hx-trigger="click" hx-target="#data_div" hx-swap="outerHTML">...</a>""" in response.text
  assert mock_called(sp)  

# Mocks
def mock_study_page_none(mocker):
  mock = mocker.patch("app.database.study.Study.page")
  mock.side_effect = [{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  return mock

def mock_study_page(mocker):
  mock = mocker.patch("app.database.study.Study.page")
  items = [
    {'sponsor': 'ACME', 'sponsor_identifier': 'ACME', 'title': 'A study for X', 'versions': 1, 'phase': "Phase 1", 'import_type': "DOCX"},
    {'sponsor': 'Big Pharma', 'sponsor_identifier': 'BP', 'title': 'A study for Y', 'versions': 2, 'phase': "Phase 1", 'import_type': "XLSX"},
    {'sponsor': 'Big Pharma', 'sponsor_identifier': 'BP', 'title': 'A study for Z', 'versions': 3, 'phase': "Phase 4", 'import_type': "FHIR"}
  ]
  mock.side_effect = [{'page': 1, 'size': 12, 'count': 3, 'filter': '', 'items': items}]
  return mock

def mock_study_page_many(mocker):
  items = []
  mock = mocker.patch("app.database.study.Study.page")
  for index in range(12):
    items.append({'sponsor': 'ACME', 'sponsor_identifier': 'ACME', 'title': 'A study for X', 'versions': 1, 'phase': "Phase 1", 'import_type': "DOCX"})
  mock.side_effect = [{'page': 1, 'size': 12, 'count': 100, 'filter': '', 'items': items}]
  return mock
