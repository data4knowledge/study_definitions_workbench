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
