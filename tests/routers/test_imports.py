import pytest
from app.configuration.configuration import application_configuration
from tests.mocks.file_mocks import protect_endpoint, mock_client, mock_async_client
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import mock_user_check_exists
from tests.mocks.factory_mocks import factory_file_import
from usdm_info import __model_version__ as usdm_version


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_import_m11(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/import/m11")
    assert response.status_code == 200
    assert '<h4 class="card-title">Import M11 Protocol</h4>' in response.text
    assert """<p>Select a single M11 file</p>""" in response.text
    assert mock_called(uc)


def test_import_xl(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/import/xl")
    assert response.status_code == 200
    assert '<h4 class="card-title">Import USDM Excel Definition</h4>' in response.text
    assert (
        "<p>Select a single Excel file and zero, one or more images files. </p>"
        in response.text
    )
    assert mock_called(uc)


def test_import_usdm3(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/import/usdm3")
    print(f"RESPONSE: {response.text}")
    assert response.status_code == 200
    assert '<h4 class="card-title">Import USDM JSON</h4>' in response.text
    assert "Import for USDM version 3.0.0" in response.text
    assert mock_called(uc)


def test_import_usdm4(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/import/usdm")
    assert response.status_code == 200
    assert '<h4 class="card-title">Import USDM JSON</h4>' in response.text
    assert f"Import for USDM version {usdm_version}" in response.text
    assert mock_called(uc)


@pytest.mark.anyio
async def test_import_m11_execute(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    pm11 = mock_process_m11(mocker)
    response = await async_client.post("/import/m11")
    assert response.status_code == 200
    assert "<h1>Fake M11 Response</h1>" in response.text
    assert mock_called(uc)
    assert mock_called(pm11)


def mock_process_m11(mocker):
    mock = mocker.patch("app.routers.imports.process_m11")
    mock.side_effect = ["<h1>Fake M11 Response</h1>"]
    return mock


@pytest.mark.anyio
async def test_import_xl_execute(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    pxl = mock_process_xl(mocker)
    response = await async_client.post("/import/xl")
    assert response.status_code == 200
    assert "<h1>Fake XL Response</h1>" in response.text
    assert mock_called(uc)
    assert mock_called(pxl)


def mock_process_xl(mocker):
    mock = mocker.patch("app.routers.imports.process_xl")
    mock.side_effect = ["<h1>Fake XL Response</h1>"]
    return mock


def test_import_status(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    response = client.get("/import/status?page=1&size=10&filter=")
    assert response.status_code == 200
    assert '<h5 class="card-title">Import Status</h5>' in response.text
    assert mock_called(uc)


def test_import_status_data(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fip = mock_file_import_page(mocker)
    response = client.get("/import/status/data?page=1&size=10&filter=")
    assert response.status_code == 200
    assert '<div id="data_div">' in response.text
    assert '<th scope="col">Imported At</th>' in response.text
    assert mock_called(uc)
    assert mock_called(fip)


def mock_file_import_page(mocker):
    mock = mocker.patch("app.database.file_import.FileImport.page")
    mock.side_effect = [{"page": 1, "size": 10, "count": 0, "filter": "", "items": []}]
    return mock


def test_import_errors(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fif = mock_file_import_find(mocker)
    dfp = mock_data_file_path(mocker)
    response = client.get("/import/1/errors")
    assert response.status_code == 200
    assert "Test File" in response.text
    assert mock_called(uc)
    assert mock_called(fif)
    assert mock_called(dfp)


def test_import_errors_error(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fif = mock_file_import_find(mocker)
    dfp = mock_data_file_path_error(mocker)
    response = client.get("/import/1/errors")
    assert response.status_code == 200
    assert '<p class="lead text-danger">Fatal Error</p>' in response.text
    assert (
        "<p>Something went wrong downloading the errors file for the import</p>"
        in response.text
    )
    assert mock_called(uc)
    assert mock_called(fif)
    assert mock_called(dfp)


def mock_file_import_find(mocker):
    mock = mocker.patch("app.database.file_import.FileImport.find")
    mock.side_effect = [factory_file_import()]
    return mock


def mock_data_file_path(mocker):
    mock = mocker.patch("app.model.file_handling.data_files.DataFiles.path")
    mock.side_effect = [("tests/test_files/main/simple.txt", "simple.txt", True)]
    return mock


def mock_data_file_path_error(mocker):
    mock = mocker.patch("app.model.file_handling.data_files.DataFiles.path")
    mock.side_effect = [("", "", False)]
    return mock
