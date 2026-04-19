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


# --- M11 docx validation ------------------------------------------------


def test_validate_m11_docx_get(mocker, monkeypatch):
    """GET serves the file picker for an M11 ``.docx``."""
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/validate/m11-docx")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_validate_m11_docx_post(mocker, monkeypatch):
    """POST runs USDM4M11.validate_docx and renders the M11 results page."""
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fh = mocker.patch("app.routers.validate.FormHandler")
    fh_instance = fh.return_value
    fh_instance.get_files = AsyncMock(
        return_value=(
            {"filename": "protocol.docx", "contents": b"docx bytes"},
            [],
            ["File accepted"],
        )
    )
    df = mocker.patch("app.routers.validate.DataFiles")
    df_instance = df.return_value
    df_instance.new.return_value = "test-uuid"
    df_instance.save.return_value = ("/tmp/protocol.docx", "protocol.docx")
    df_instance.path.return_value = (
        "tests/test_files/main/simple.txt",
        "simple.txt",
        True,
    )
    df_instance.delete.return_value = True

    usdm4m11 = mocker.patch("app.routers.validate.USDM4M11")
    instance = usdm4m11.return_value
    results_mock = MagicMock()
    results_mock.to_dict.return_value = [
        {
            "rule_id": "M11_001",
            "severity": "error",
            "status": "Failed",
            "message": "Required element 'Full Title' is missing.",
            "expected": "A value of type 'Text'",
            "actual": "(no value)",
            "element_name": "Full Title",
            "section_number": "",
            "section_title": "Title Page",
        }
    ]
    instance.validate_docx.return_value = results_mock

    response = await async_client.post("/validate/m11-docx")
    assert response.status_code == 200
    assert mock_called(uc)
    instance.validate_docx.assert_called_once()
    # Lock in the DataFiles convention: the route must use the existing
    # "docx" media_type. Inventing a new one (e.g. "m11") raises KeyError
    # from DataFiles.path — a hazard we already hit once.
    save_type = df_instance.save.call_args.args[0]
    path_type = df_instance.path.call_args.args[0]
    assert save_type == "docx"
    assert path_type == "docx"


@pytest.mark.anyio
async def test_validate_m11_docx_post_extraction_failure(mocker, monkeypatch):
    """If USDM4M11.validate_docx returns None (extraction failed), the
    response still renders without throwing and surfaces a message."""
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    mock_user_check_exists(mocker)
    fh = mocker.patch("app.routers.validate.FormHandler")
    fh_instance = fh.return_value
    fh_instance.get_files = AsyncMock(
        return_value=(
            {"filename": "broken.docx", "contents": b"not a docx"},
            [],
            ["File accepted"],
        )
    )
    df = mocker.patch("app.routers.validate.DataFiles")
    df_instance = df.return_value
    df_instance.new.return_value = "test-uuid"
    df_instance.save.return_value = ("/tmp/broken.docx", "broken.docx")
    df_instance.path.return_value = (
        "tests/test_files/main/simple.txt",
        "simple.txt",
        True,
    )
    df_instance.delete.return_value = True

    usdm4m11 = mocker.patch("app.routers.validate.USDM4M11")
    usdm4m11.return_value.validate_docx.return_value = None

    response = await async_client.post("/validate/m11-docx")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_validate_m11_docx_post_no_file(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    mock_user_check_exists(mocker)
    fh = mocker.patch("app.routers.validate.FormHandler")
    fh_instance = fh.return_value
    fh_instance.get_files = AsyncMock(return_value=(None, [], ["No file"]))
    response = await async_client.post("/validate/m11-docx")
    assert response.status_code == 200
