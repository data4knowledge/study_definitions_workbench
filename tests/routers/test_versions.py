import pytest
from unittest.mock import MagicMock
from app.database.version import Version
from app.configuration.configuration import application_configuration
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import mock_user_check_exists
from tests.mocks.fastapi_mocks import protect_endpoint, mock_client
from tests.mocks.utility_mocks import (
    mock_transmit_role_enabled_true,
    mock_transmit_role_enabled_false,
)
from tests.mocks.usdm_json_mocks import mock_usdm_json_init, mock_usdm_study_version, mock_usdm_json_templates
from tests.mocks.fhir_version_mocks import mock_fhir_versions
from tests.mocks.file_mocks import mock_file_import_find


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
    ujt = mock_usdm_json_templates(mocker, "app.routers.versions")
    fv = mock_fhir_versions(mocker, "app.routers.versions")
    response = client.get("/versions/1/summary")
    # print(f"RESPONSE: {response.text}")
    assert response.status_code == 200
    assert (
        """<a class="dropdown-item" href="/transmissions/status?page=1&size=10">Transmission Status</a>"""
        in response.text
    )
    assert """M11 FHIR, Dallas (PRISM 2) (.json)""" in response.text
    assert mock_called(uc)
    assert mock_called(ift)
    assert mock_called(uji)
    assert mock_called(usv)
    assert mock_called(ujt)
    assert mock_called(fv)
    assert_view_menu(response.text, "summary", templates=["M11"])


def test_version_summary_fhir_not_authorised(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    ift = mock_transmit_role_enabled_false(mocker, "app.routers.versions")
    uji = mock_usdm_json_init(mocker, "app.routers.versions")
    usv = mock_usdm_study_version(mocker, "app.routers.versions")
    ujt = mock_usdm_json_templates(mocker, "app.routers.versions")
    fv = mock_fhir_versions(mocker, "app.routers.versions")
    response = client.get("/versions/1/summary")
    # print(f"RESPONSE: {response.text}")
    assert response.status_code == 200
    assert """Transmission Status""" not in response.text
    assert mock_called(uc)
    assert mock_called(ift)
    assert mock_called(uji)
    assert mock_called(usv)
    assert mock_called(ujt)
    assert mock_called(fv)
    assert_view_menu(response.text, "summary", templates=["M11"])


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
    assert (
        "Error downloading the requested Excel (USDM v4) format file" in response.text
    )

    # Verify the mocks were called correctly
    assert mock_called(uc)
    assert mock_called(mock_usdm_db_init)
    assert mock_called(mock_usdm_db_excel)


def assert_view_menu(text, type, templates=None):
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
    if type != "protocol" and templates:
        for template in templates:
            assert (
                f'<a class="dropdown-item" href="/versions/1/protocol?template={template}">{template} Protocol</a>'
                in text
            )
    if type != "history":
        assert (
            '<a class="dropdown-item" href="/versions/1/history">Version History</a>'
            in text
        )


def test_import_xl_get(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False, "os": True, "pfda": False, "source": "os",
    }
    response = client.get("/versions/1/load/costs")
    assert response.status_code == 200
    assert mock_called(uc)


def test_protocol_m11(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    uji = mock_usdm_json_init(mocker, "app.routers.versions")
    usv = mock_usdm_study_version(mocker, "app.routers.versions")
    mocker.patch("app.routers.versions.USDMJson.json", return_value=(
        "tests/test_files/main/simple.txt", "simple.txt", "application/json"
    ))
    mocker.patch("app.routers.versions.USDM4M11").return_value.to_html.return_value = "<p>Protocol</p>"
    response = client.get("/versions/1/protocol?template=M11")
    assert response.status_code == 200
    assert mock_called(uc)


def test_protocol_cpt(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    uji = mock_usdm_json_init(mocker, "app.routers.versions")
    usv = mock_usdm_study_version(mocker, "app.routers.versions")
    mocker.patch("app.routers.versions.USDMJson.json", return_value=(
        "tests/test_files/main/simple.txt", "simple.txt", "application/json"
    ))
    mocker.patch("app.routers.versions.USDM4CPT").return_value.to_html.return_value = "<p>CPT</p>"
    response = client.get("/versions/1/protocol?template=CPT")
    assert response.status_code == 200
    assert mock_called(uc)


def test_protocol_no_file(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    uji = mock_usdm_json_init(mocker, "app.routers.versions")
    mocker.patch("app.routers.versions.USDMJson.json", return_value=("", "", ""))
    response = client.get("/versions/1/protocol?template=M11")
    assert response.status_code == 200
    assert "Error locating the USDM JSON file" in response.text
    assert mock_called(uc)


def test_export_protocol_success(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    files_mock = MagicMock()
    files_mock.save.return_value = ("tests/test_files/main/simple.txt", "simple.txt")
    def custom_init(self, *args, **kwargs):
        self._files = files_mock
    mocker.patch("app.routers.versions.USDMJson.__init__", new=custom_init)
    mocker.patch("app.routers.versions.USDMJson.json", return_value=(
        "tests/test_files/main/simple.txt", "simple.txt", "application/json"
    ))
    mocker.patch("app.routers.versions.USDM4M11").return_value.to_html.return_value = "<p>Protocol</p>"
    response = client.get("/versions/1/protocol/export?template=M11")
    assert response.status_code == 200
    assert mock_called(uc)


def test_export_protocol_error(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    files_mock = MagicMock()
    files_mock.save.return_value = ("", "")
    def custom_init(self, *args, **kwargs):
        self._files = files_mock
    mocker.patch("app.routers.versions.USDMJson.__init__", new=custom_init)
    mocker.patch("app.routers.versions.USDMJson.json", return_value=(
        "tests/test_files/main/simple.txt", "simple.txt", "application/json"
    ))
    mocker.patch("app.routers.versions.USDM4M11").return_value.to_html.return_value = "<p>Protocol</p>"
    response = client.get("/versions/1/protocol/export?template=M11")
    assert response.status_code == 200
    assert "Error downloading the requested protocol" in response.text
    assert mock_called(uc)


def test_protocol_other(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    uji = mock_usdm_json_init(mocker, "app.routers.versions")
    usv = mock_usdm_study_version(mocker, "app.routers.versions")
    mocker.patch("app.routers.versions.USDMJson.json", return_value=(
        "tests/test_files/main/simple.txt", "simple.txt", "application/json"
    ))
    mock_wrapper = MagicMock()
    mock_wrapper.to_html.return_value = "<p>Other Protocol</p>"
    mocker.patch("app.routers.versions.USDMJson.wrapper", return_value=mock_wrapper)
    response = client.get("/versions/1/protocol?template=OTHER")
    assert response.status_code == 200
    assert mock_called(uc)


@pytest.mark.anyio
async def test_versions_post_load_success(mocker, monkeypatch):
    from unittest.mock import AsyncMock
    from tests.mocks.fastapi_mocks import mock_async_client
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    def custom_init(self, *args, **kwargs):
        self.uuid = "test-uuid"
    mocker.patch("app.routers.versions.USDMJson.__init__", new=custom_init)
    fh = mocker.patch("app.routers.versions.FormHandler")
    fh_instance = fh.return_value
    fh_instance.get_files = AsyncMock(return_value=(
        {"filename": "costs.yaml", "contents": b"key: value"},
        None,
        ["File accepted"],
    ))
    df = mocker.patch("app.routers.versions.DataFiles")
    df_instance = df.return_value
    df_instance.save.return_value = ("/tmp/costs.yaml", "costs.yaml")
    mocker.patch("app.routers.versions.yaml.safe_load", return_value={"key": "value"})
    response = await async_client.post("/versions/1/load/costs")
    assert response.status_code == 200
    assert mock_called(uc)


@pytest.mark.anyio
async def test_versions_post_load_failure(mocker, monkeypatch):
    from unittest.mock import AsyncMock
    from tests.mocks.fastapi_mocks import mock_async_client
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    def custom_init(self, *args, **kwargs):
        self.uuid = "test-uuid"
    mocker.patch("app.routers.versions.USDMJson.__init__", new=custom_init)
    fh = mocker.patch("app.routers.versions.FormHandler")
    fh_instance = fh.return_value
    fh_instance.get_files = AsyncMock(return_value=(
        {"filename": "costs.yaml", "contents": b"key: value"},
        None,
        [],
    ))
    df = mocker.patch("app.routers.versions.DataFiles")
    df_instance = df.return_value
    df_instance.save.return_value = (None, None)
    mocker.patch("app.routers.versions.yaml.safe_load", return_value={"key": "value"})
    response = await async_client.post("/versions/1/load/costs")
    assert response.status_code == 200
    assert mock_called(uc)
