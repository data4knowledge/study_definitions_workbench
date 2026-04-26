import pytest
from app.configuration.configuration import application_configuration
from tests.mocks.fastapi_mocks import protect_endpoint, mock_client, mock_async_client
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
    response = client.get("/import/m11-docx")
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
    # mock = mocker.patch("app.routers.imports.process_m11")
    mock = mocker.patch("app.imports.request_handler.RequestHandler.process")
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
    # mock = mocker.patch("app.routers.imports.process_xl")
    mock = mocker.patch("app.imports.request_handler.RequestHandler.process")
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
    # Validation column is present alongside the existing errors column
    assert '<th scope="col">Validation</th>' in response.text
    assert mock_called(uc)
    assert mock_called(fip)


def test_import_status_data_renders_m11_validation_link(mocker, monkeypatch):
    """M11 items in the import list must expose a link to the
    /import/{id}/m11-validation view; non-M11 items must not."""
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fip = mocker.patch("app.database.file_import.FileImport.page")
    fip.side_effect = [
        {
            "page": 1,
            "size": 10,
            "count": 2,
            "filter": "",
            "items": [
                {
                    "id": 42,
                    "type": "M11_DOCX",
                    "created": "2026-04-20",
                    "filename": "protocol.docx",
                    "status": "Success",
                },
                {
                    "id": 43,
                    "type": "USDM_EXCEL",
                    "created": "2026-04-20",
                    "filename": "study.xlsx",
                    "status": "Success",
                },
            ],
        }
    ]
    response = client.get("/import/status/data?page=1&size=10&filter=")
    assert response.status_code == 200
    body = response.text
    assert 'href="/import/42/m11-validation"' in body
    assert "M11 Findings" in body
    # Non-M11 row must not surface the link
    assert 'href="/import/43/m11-validation"' not in body
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


def test_import_m11_validation(mocker, monkeypatch):
    """Happy path — persisted findings render in the shared results
    table with severity pills, rule ids, and the M11 download form."""
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fif = mock_file_import_find(mocker)
    dfr = mocker.patch(
        "app.model.file_handling.data_files.DataFiles.read",
        return_value=(
            '[{"rule_id":"M11_001","severity":"error","section":"1",'
            '"element":"Full Title",'
            '"message":"Required element \'Full Title\' is missing.",'
            '"rule_text":"","path":""}]'
        ),
    )
    response = client.get("/import/1/m11-validation")
    assert response.status_code == 200
    body = response.text
    assert "M11 Validation Findings" in body
    assert "M11_001" in body
    assert "Full Title" in body
    # Jinja autoescape converts apostrophes to ``&#39;`` in HTML output —
    # the rendered cell carries the escaped form, not the raw string.
    assert "Required element &#39;Full Title&#39; is missing." in body
    # Download form is present when findings are non-empty
    assert 'formaction="/validate/download/csv"' in body
    assert 'value="m11-findings"' in body
    assert mock_called(uc)
    assert mock_called(fif)
    assert mock_called(dfr)


def test_import_m11_validation_no_file(mocker, monkeypatch):
    """When no findings file has been persisted (non-M11 import, legacy
    import, or validator exception), the page renders an informational
    message rather than an error. Validator findings are advisory."""
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fif = mock_file_import_find(mocker)
    dfr = mocker.patch(
        "app.model.file_handling.data_files.DataFiles.read",
        return_value=None,
    )
    response = client.get("/import/1/m11-validation")
    assert response.status_code == 200
    assert (
        "No M11 validation findings are available for this import."
        in response.text
    )
    # No download form when findings are empty
    assert 'formaction="/validate/download/csv"' not in response.text
    assert mock_called(uc)
    assert mock_called(fif)
    assert mock_called(dfr)


def test_import_m11_validation_corrupted(mocker, monkeypatch):
    """If the persisted file isn't valid JSON the page should report a
    decode problem and still render — not 500."""
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    fif = mock_file_import_find(mocker)
    dfr = mocker.patch(
        "app.model.file_handling.data_files.DataFiles.read",
        return_value="this is not json",
    )
    response = client.get("/import/1/m11-validation")
    assert response.status_code == 200
    assert (
        "M11 validation file could not be decoded"
        in response.text
    )
    assert mock_called(uc)
    assert mock_called(fif)
    assert mock_called(dfr)


def test_import_cpt_docx(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/import/cpt-docx")
    assert response.status_code == 200
    assert mock_called(uc)


def test_import_legacy_pdf(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    response = client.get("/import/legacy-pdf")
    assert response.status_code == 200
    assert mock_called(uc)


def test_import_fhir_valid(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    from tests.mocks.factory_mocks import factory_user

    uc = mocker.patch("app.database.user.User.check")
    uc.return_value = (factory_user(), True)
    application_configuration.file_picker = {
        "browser": False,
        "os": True,
        "pfda": False,
        "source": "os",
    }
    mocker.patch(
        "app.routers.imports.check_fhir_version",
        return_value=(True, "PRISM 2"),
    )
    response = client.get("/import/fhir?version=prism2")
    assert response.status_code == 200
    assert mock_called(uc, 2)


def test_import_fhir_invalid(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    mocker.patch(
        "app.routers.imports.check_fhir_version",
        return_value=(False, ""),
    )
    response = client.get("/import/fhir?version=invalid")
    assert response.status_code == 200
    assert "Invalid FHIR version" in response.text
    assert mock_called(uc)


@pytest.mark.anyio
async def test_import_cpt_docx_execute(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    pm = mocker.patch("app.imports.request_handler.RequestHandler.process")
    pm.side_effect = ["<h1>Fake CPT Response</h1>"]
    response = await async_client.post("/import/cpt-docx")
    assert response.status_code == 200
    assert mock_called(uc)
    assert mock_called(pm)


@pytest.mark.anyio
async def test_import_legacy_pdf_execute(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    pm = mocker.patch("app.imports.request_handler.RequestHandler.process")
    pm.side_effect = ["<h1>Fake Legacy Response</h1>"]
    response = await async_client.post("/import/legacy-pdf")
    assert response.status_code == 200
    assert mock_called(uc)
    assert mock_called(pm)


@pytest.mark.anyio
async def test_import_fhir_execute(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    pm = mocker.patch("app.imports.request_handler.RequestHandler.process")
    pm.side_effect = ["<h1>Fake FHIR Response</h1>"]
    response = await async_client.post("/import/fhir?version=prism3")
    assert response.status_code == 200
    assert mock_called(uc)
    assert mock_called(pm)


@pytest.mark.anyio
async def test_import_usdm3_execute(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    pm = mocker.patch("app.imports.request_handler.RequestHandler.process")
    pm.side_effect = ["<h1>Fake USDM3 Response</h1>"]
    response = await async_client.post("/import/usdm3")
    assert response.status_code == 200
    assert mock_called(uc)
    assert mock_called(pm)


@pytest.mark.anyio
async def test_import_usdm4_execute(mocker, monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    pm = mocker.patch("app.imports.request_handler.RequestHandler.process")
    pm.side_effect = ["<h1>Fake USDM4 Response</h1>"]
    response = await async_client.post("/import/usdm")
    assert response.status_code == 200
    assert mock_called(uc)
    assert mock_called(pm)
