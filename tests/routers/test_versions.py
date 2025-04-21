import pytest
from app.database.version import Version
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import *
from tests.mocks.fastapi_mocks import *
from tests.mocks.utility_mocks import *
from tests.mocks.usdm_json_mocks import *
from tests.mocks.fhir_version_mocks import *
from tests.mocks.file_mocks import *
from fastapi.responses import FileResponse


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_version_summary_fhir_authorised(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    ift = mock_transmit_role_enabled_true(mocker, "app.routers.versions")
    uji = mock_usdm_json_init(mocker, "app.routers.versions")
    usv = mock_usdm_study_version(mocker, "app.routers.versions")
    fv = mock_fhir_versions(mocker, "app.routers.versions")
    # We could do better here but for now will do
    # fvd = mock_fhir_version_description(mocker, 'app.main.templates')
    response = client.get("/versions/1/summary")
    # print(f"RESPONSE: {response.text}")
    assert response.status_code == 200
    assert (
        """<a class="dropdown-item" href="/transmissions/status?page=1&size=10">Transmission Status</a>"""
        in response.text
    )
    assert """M11 FHIR v3, FHIR Version not supported""" in response.text
    assert mock_called(uc)
    assert mock_called(ift)
    assert mock_called(uji)
    assert mock_called(usv)
    assert mock_called(fv)
    assert_view_menu(response.text, "summary")


def test_version_summary_fhir_not_authorised(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    ift = mock_transmit_role_enabled_false(mocker, "app.routers.versions")
    uji = mock_usdm_json_init(mocker, "app.routers.versions")
    usv = mock_usdm_study_version(mocker, "app.routers.versions")
    fv = mock_fhir_versions(mocker, "app.routers.versions")
    response = client.get("/versions/1/summary")
    # print(f"RESPONSE: {response.text}")
    assert response.status_code == 200
    assert """Transmission Status""" not in response.text
    assert """M11 FHIR v3, FHIR Version not supported""" in response.text
    assert mock_called(uc)
    assert mock_called(ift)
    assert mock_called(uji)
    assert mock_called(usv)
    assert mock_called(fv)
    assert_view_menu(response.text, "summary")


def test_version_history(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    usv = mock_usdm_study_version(mocker)
    uji = mock_usdm_json_init(mocker)
    response = client.get("/versions/1/history")
    assert response.status_code == 200
    assert (
        '<h5 class="card-title">Version History: The Offical Study Title For Test</h5>'
        in response.text
    )
    assert (
        '<h6 class="card-subtitle mb-2 text-muted">Sponsor: Identifier For Test | Phase: Phase For Test | Identifier:  | Version: 1</h6>'
        in response.text
    )
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
    assert "<td>1</td>" in response.text
    assert mock_called(vf)
    assert mock_called(vp)
    assert mock_called(fif)


def mock_version_find(mocker):
    mock = mocker.patch("app.database.version.Version.find")
    mock.side_effect = [factory_version()]
    return mock


def mock_version_page(mocker):
    mock = mocker.patch("app.database.version.Version.page")
    mock.side_effect = [
        {
            "page": 1,
            "size": 10,
            "count": 1,
            "filter": "",
            "items": [factory_version().model_dump()],
        }
    ]
    return mock


def factory_version() -> Version:
    return Version(**{"version": "1", "id": 1, "import_id": 1, "study_id": 1})


def test_export_excel_success(mocker, monkeypatch):
    """Test the export_excel route when the Excel file is successfully generated."""
    # Create a mock response object
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200

    # Set up the test client
    client = mock_client(monkeypatch)

    # Mock the dependencies
    mock_user_check = mock_user_check_exists(mocker)
    mock_user_check.return_value = (
        mocker.MagicMock(),
        True,
    )  # Return a mock user and True

    # Mock USDMDatabase initialization and excel method
    mock_usdm_db_init = mocker.patch(
        "app.usdm_database.usdm_database.USDMDatabase.__init__"
    )
    mock_usdm_db_init.return_value = None

    mock_usdm_db_excel = mocker.patch(
        "app.usdm_database.usdm_database.USDMDatabase.excel"
    )
    mock_usdm_db_excel.return_value = (
        "/path/to/excel.xlsx",
        "excel.xlsx",
        "application/vnd.ms-excel",
    )

    # Mock FileResponse to return our mock response
    mock_file_response = mocker.patch("app.routers.versions.FileResponse")
    mock_file_response.return_value = mock_response

    # Call the endpoint
    response = client.get("/versions/1/export/excel")

    # Verify the response
    assert response.status_code == 200

    # Verify the mocks were called correctly
    mock_usdm_db_init.assert_called_once()
    mock_usdm_db_excel.assert_called_once()
    mock_file_response.assert_called_once_with(
        path="/path/to/excel.xlsx",
        filename="excel.xlsx",
        media_type="application/vnd.ms-excel",
    )


def test_export_excel_failure(mocker, monkeypatch):
    """Test the export_excel route when the Excel file generation fails."""
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)

    # Mock USDMDatabase initialization and excel method
    mock_usdm_db_init = mocker.patch(
        "app.usdm_database.usdm_database.USDMDatabase.__init__"
    )
    mock_usdm_db_init.return_value = None

    # Return None to simulate failure
    mock_usdm_db_excel = mocker.patch(
        "app.usdm_database.usdm_database.USDMDatabase.excel"
    )
    mock_usdm_db_excel.return_value = (None, None, None)

    response = client.get("/versions/1/export/excel")

    # Verify the response
    assert response.status_code == 200
    assert "Error downloading the requested Excel file" in response.text

    # Verify the mocks were called correctly
    assert mock_called(uc)
    assert mock_called(mock_usdm_db_init)
    assert mock_called(mock_usdm_db_excel)


def assert_view_menu(text, type):
    if type != "summary":
        assert (
            '<a class="dropdown-item" href="/versions/1/summary">Summary View</a>'
            in text
        )
    if type != "safety":
        assert (
            '<a class="dropdown-item" href="/versions/1/safety">Safety View</a>' in text
        )
    if type != "statisitcs":
        assert (
            '<a class="dropdown-item" href="/versions/1/statistics">Statistics View</a>'
            in text
        )
    if type != "protocol":
        assert (
            '<a class="dropdown-item" href="/versions/1/protocol">Protocol</a>' in text
        )
    if type != "history":
        assert (
            '<a class="dropdown-item" href="/versions/1/protocol">Protocol</a>' in text
        )
