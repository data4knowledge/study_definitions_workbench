import pytest
from unittest.mock import MagicMock
from tests.mocks.general_mocks import mock_called
from tests.mocks.fastapi_mocks import protect_endpoint, mock_client
from tests.mocks.usdm_json_mocks import (
    mock_usdm_json_init,
    mock_usdm_json_timelines,
    mock_usdm_json_soa,
    mock_usdm_json_fhir_soa,
    mock_usdm_json_fhir_soa_error,
)


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
    print(f"RESULT: {response.text}")
    assert (
        '<h5 class="card-title">Schedule of Activities: SOA LABEL</h5>' in response.text
    )
    assert (
        '<h6 class="card-subtitle mb-2 text-muted">SOA Description | Secondary timeline</h6>'
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


def _mock_usdm_with_files(mocker, files_mock):
    """Mock USDMJson.__init__ so it only sets _files on the instance."""
    def custom_init(self, *args, **kwargs):
        self._files = files_mock
    mocker.patch("app.routers.version_timelines.USDMJson.__init__", new=custom_init)


def test_display_patient_journey(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("tests/test_files/main/simple.txt", "simple.txt", "text/plain")
    _mock_usdm_with_files(mocker, files_mock)
    mocker.patch("app.routers.version_timelines.USDM4PJ").return_value.simple_view.return_value = {}
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/pj")
    assert response.status_code == 200


def test_display_patient_journey_error(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("", "", "")
    _mock_usdm_with_files(mocker, files_mock)
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/pj")
    assert response.status_code == 200
    assert "Error locating the USDM file" in response.text


def test_display_expansion(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("tests/test_files/main/simple.txt", "simple.txt", "text/plain")
    files_mock.exists.return_value = False
    _mock_usdm_with_files(mocker, files_mock)
    mocker.patch("app.routers.version_timelines.USDM4PJ").return_value.expanded_view.return_value = {}
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/expansion")
    assert response.status_code == 200


def test_display_expansion_with_costs(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("tests/test_files/main/simple.txt", "simple.txt", "text/plain")
    files_mock.exists.return_value = True
    _mock_usdm_with_files(mocker, files_mock)
    mocker.patch("app.routers.version_timelines.USDM4PJ").return_value.expanded_view.return_value = {}
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/expansion")
    assert response.status_code == 200


def test_export_expansion_with_costs(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("tests/test_files/main/simple.txt", "simple.txt", "text/plain")
    files_mock.exists.return_value = True
    files_mock.save.return_value = ("tests/test_files/main/simple.txt", "simple.txt")
    _mock_usdm_with_files(mocker, files_mock)
    mocker.patch("app.routers.version_timelines.USDM4PJ").return_value.expanded_view.return_value = {}
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/export/expansion")
    assert response.status_code == 200


def test_display_expansion_no_usdm(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("", "", "")
    _mock_usdm_with_files(mocker, files_mock)
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/expansion")
    assert response.status_code == 200
    assert "Error locating the USDM file" in response.text


def test_export_expansion(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("tests/test_files/main/simple.txt", "simple.txt", "text/plain")
    files_mock.exists.return_value = False
    files_mock.save.return_value = ("tests/test_files/main/simple.txt", "simple.txt")
    _mock_usdm_with_files(mocker, files_mock)
    mocker.patch("app.routers.version_timelines.USDM4PJ").return_value.expanded_view.return_value = {}
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/export/expansion")
    assert response.status_code == 200


def test_export_expansion_error(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("", "", "")
    _mock_usdm_with_files(mocker, files_mock)
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/export/expansion")
    assert response.status_code == 200
    assert "Error downloading the requested JSON file" in response.text


def test_export_patient_journey(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("tests/test_files/main/simple.txt", "simple.txt", "text/plain")
    files_mock.save.return_value = ("tests/test_files/main/simple.txt", "simple.txt")
    _mock_usdm_with_files(mocker, files_mock)
    mocker.patch("app.routers.version_timelines.USDM4PJ").return_value.simple_view.return_value = {}
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/export/pj")
    assert response.status_code == 200


def test_export_patient_journey_error(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    files_mock = MagicMock()
    files_mock.path.return_value = ("", "", "")
    _mock_usdm_with_files(mocker, files_mock)
    response = client.get("/versions/1/studyDesigns/d1/timelines/t1/export/pj")
    assert response.status_code == 200
    assert "Error downloading the requested JSON file" in response.text


def test_timeline_transmit(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mocker.patch("app.routers.version_timelines.run_fhir_soa_transmit")
    response = client.get(
        "/versions/1/studyDesigns/d1/timelines/t1/transmit/ep1", follow_redirects=False
    )
    assert response.status_code == 307
