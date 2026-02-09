import pytest
from unittest.mock import AsyncMock, MagicMock
from app.configuration.configuration import application_configuration
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import mock_user_check_exists
from tests.mocks.fastapi_mocks import protect_endpoint, mock_client, mock_async_client


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_validate_usdm3_get(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/validate/usdm3")
    assert response.status_code == 200


def test_validate_usdm_get(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/validate/usdm")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_validate_usdm3_post(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fh = mocker.patch("app.routers.validate.FormHandler")
    fh_instance = fh.return_value
    fh_instance.get_files = AsyncMock(
        return_value=(
            {"filename": "test.json", "contents": b'{"test": true}'},
            [],
            ["File accepted"],
        )
    )
    df = mocker.patch("app.routers.validate.DataFiles")
    df_instance = df.return_value
    df_instance.new.return_value = "test-uuid"
    df_instance.save.return_value = ("/tmp/test.json", "test.json")
    df_instance.path.return_value = (
        "tests/test_files/main/simple.txt",
        "simple.txt",
        True,
    )
    df_instance.delete.return_value = True
    usdm3 = mocker.patch("app.routers.validate.USDM3")
    usdm3_instance = usdm3.return_value
    results_mock = MagicMock()
    results_mock.to_dict.return_value = {"errors": []}
    usdm3_instance.validate.return_value = results_mock
    response = await async_client.post("/validate/usdm3")
    assert response.status_code == 200
    assert mock_called(uc)


@pytest.mark.anyio
async def test_validate_usdm_post(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fh = mocker.patch("app.routers.validate.FormHandler")
    fh_instance = fh.return_value
    fh_instance.get_files = AsyncMock(
        return_value=(
            {"filename": "test.json", "contents": b'{"test": true}'},
            [],
            ["File accepted"],
        )
    )
    df = mocker.patch("app.routers.validate.DataFiles")
    df_instance = df.return_value
    df_instance.new.return_value = "test-uuid"
    df_instance.save.return_value = ("/tmp/test.json", "test.json")
    df_instance.path.return_value = (
        "tests/test_files/main/simple.txt",
        "simple.txt",
        True,
    )
    df_instance.delete.return_value = True
    usdm4 = mocker.patch("app.routers.validate.USDM4")
    usdm4_instance = usdm4.return_value
    results_mock = MagicMock()
    results_mock.to_dict.return_value = {"errors": []}
    usdm4_instance.validate.return_value = results_mock
    response = await async_client.post("/validate/usdm")
    assert response.status_code == 200
    assert mock_called(uc)


@pytest.mark.anyio
async def test_validate_post_no_file(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fh = mocker.patch("app.routers.validate.FormHandler")
    fh_instance = fh.return_value
    fh_instance.get_files = AsyncMock(return_value=(None, [], ["No file"]))
    response = await async_client.post("/validate/usdm3")
    assert response.status_code == 200
    assert mock_called(uc)
