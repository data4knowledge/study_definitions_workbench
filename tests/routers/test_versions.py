import pytest
from app.database.version import Version
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import *
from tests.mocks.fastapi_mocks import *
from tests.mocks.utility_mocks import *
from tests.mocks.usdm_json_mocks import *
from tests.mocks.fhir_version_mocks import *
from tests.mocks.file_mocks import *

@pytest.fixture
def anyio_backend():
  return 'asyncio'

def test_version_summary_fhir_authorised(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  uc = mock_user_check_exists(mocker)
  ift = mock_is_fhir_tx_true(mocker, 'app.routers.versions')
  uji = mock_usdm_json_init(mocker, 'app.routers.versions')
  usv = mock_usdm_study_version(mocker, 'app.routers.versions')
  fv = mock_fhir_versions(mocker, 'app.routers.versions')
  # We could do better here but for now will do
  #fvd = mock_fhir_version_description(mocker, 'app.main.templates')
  response = client.get("/versions/1/summary")
  #print(f"RESPONSE: {response.text}")
  assert response.status_code == 200
  assert """<a class="dropdown-item" href="/transmissions/status?page=1&size=10">Transmission Status</a>""" in response.text
  assert """M11 FHIR v3, FHIR Version not supported""" in response.text
  assert mock_called(uc)
  assert mock_called(ift)
  assert mock_called(uji)
  assert mock_called(usv)
  assert mock_called(fv)
  assert_view_menu(response.text, 'summary')

def test_version_summary_fhir_not_authorised(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  uc = mock_user_check_exists(mocker)
  ift = mock_is_fhir_tx_false(mocker, 'app.routers.versions')
  uji = mock_usdm_json_init(mocker, 'app.routers.versions')
  usv = mock_usdm_study_version(mocker, 'app.routers.versions')
  fv = mock_fhir_versions(mocker, 'app.routers.versions')
  response = client.get("/versions/1/summary")
  #print(f"RESPONSE: {response.text}")
  assert response.status_code == 200
  assert """Transmission Status""" not in response.text
  assert """M11 FHIR v3, FHIR Version not supported""" in response.text
  assert mock_called(uc)
  assert mock_called(ift)
  assert mock_called(uji)
  assert mock_called(usv)
  assert mock_called(fv)
  assert_view_menu(response.text, 'summary')

def test_version_history(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  uc = mock_user_check_exists(mocker)
  usv = mock_usdm_study_version(mocker)
  uji = mock_usdm_json_init(mocker)
  response = client.get("/versions/1/history")
  assert response.status_code == 200
  assert '<h5 class="card-title">Version History</h5>' in response.text
  assert ' <h6 class="card-subtitle mb-2 text-muted">Title: The Offical Study Title For Test | Sponsor: Identifier For Test| Phase: Phase For Test | Identifier:</h6>' in response.text
  assert mock_called(uc)
  assert mock_called(usv)
  assert mock_called(uji)
  assert_view_menu(response.text, "history")

def test_version_history_data(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  vf = mock_version_find(mocker)
  vp = mock_version_page(mocker)
  fif = mock_file_import_find(mocker)
  response = client.get("/versions/1/history/data?page=1&size=10&filter=")
  assert response.status_code == 200
  assert '<th scope="col">Version</th>' in response.text
  assert '<td>1</td>' in response.text
  assert mock_called(vf)
  assert mock_called(vp)
  assert mock_called(fif)

def mock_version_find(mocker):
  mock = mocker.patch("app.model.version.Version.find")
  mock.side_effect = [factory_version()]
  return mock

def mock_version_page(mocker):
  mock = mocker.patch("app.model.version.Version.page")
  mock.side_effect = [{'page': 1, 'size': 10, 'count': 1, 'filter': '', 'items': [factory_version().model_dump()]}]
  return mock

def factory_version() -> Version:
  return Version(**{'version': '1', 'id': 1, 'import_id': 1, 'study_id': 1})

def assert_view_menu(text, type):
  if type != 'summary':
    assert '<a class="dropdown-item" href="/versions/1/summary">Summary View</a>' in text
  if type != 'safety':
    assert '<a class="dropdown-item" href="/versions/1/safety">Safety View</a>' in text
  if type != 'statisitcs':
    assert '<a class="dropdown-item" href="/versions/1/statistics">Statistics View</a>' in text
  if type != 'protocol':
    assert '<a class="dropdown-item" href="/versions/1/protocol">Protocol</a>' in text
  if type != 'history':
    assert '<a class="dropdown-item" href="/versions/1/protocol">Protocol</a>' in text
