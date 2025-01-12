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
    return "asyncio"


def test_get_study_design_timelines(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uji = mock_usdm_json_init(mocker)
    ujt = mock_usdm_json_timelines(mocker)
    response = client.get("/versions/1/studyDesigns/1/timelines")
    assert response.status_code == 200
    # print(f"RESULT: {response.text}")
    assert (
        '<a href="/versions/1/studyDesigns/2/timelines/3/soa" class="btn btn-sm btn-outline-primary rounded-5">'
        in response.text
    )
    assert "Special Timeline" in response.text
    assert mock_called(uji)
    assert mock_called(ujt)


def test_get_study_design_soa(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uji = mock_usdm_json_init(mocker)
    ujs = mock_usdm_json_soa(mocker)
    response = client.get("/versions/1/studyDesigns/2/timelines/3/soa")
    assert response.status_code == 200
    # print(f"RESULT: {response.text}")
    assert (
        '<h5 class="card-title">Schedule of Activities: SOA LABEL</h5>' in response.text
    )
    assert (
        '<h6 class="card-subtitle mb-2 text-muted">Description: SOA Description | Main: False | Name: SoA Name</h6>'
        in response.text
    )
    assert mock_called(uji)
    assert mock_called(ujs)


def test_get_study_design_fhir_soa(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uji = mock_usdm_json_init(mocker)
    ujfs = mock_usdm_json_fhir_soa(mocker)
    response = client.get("/versions/1/studyDesigns/2/timelines/3/export/fhir")
    assert response.status_code == 200
    assert mock_called(uji)
    assert mock_called(ujfs)


def test_get_study_design_fhir_soa_error(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uji = mock_usdm_json_init(mocker)
    ujfs = mock_usdm_json_fhir_soa_error(mocker)
    response = client.get("/versions/1/studyDesigns/2/timelines/3/export/fhir")
    assert response.status_code == 200
    # print(f"RESULT: {response.text}")
    assert (
        "<p>Error downloading the requested FHIR SoA message file</p>" in response.text
    )
    assert mock_called(uji)
    assert mock_called(ujfs)
