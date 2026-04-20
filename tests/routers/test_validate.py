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
    # render_current produces the HTML for the annotated-document tab.
    # Stub it here so the route completes without touching real
    # Wrapper / M11Export plumbing.
    instance.render_current.return_value = (
        '<div class="ich-m11-document-div">'
        '<div data-m11-element="Full Title">A Trial</div>'
        '</div>'
    )

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
    # Annotator ran on the rendered HTML and injected a marker for the
    # single finding. Proves the annotated-document tab is wired.
    body = response.text
    assert "m11-doc-marker" in body
    assert 'data-m11-finding-index="0"' in body


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


# --- Download endpoints (one per format, server-side) ------------------
#
# Plain HTML-form POSTs, not JSON. The results template carries the
# findings JSON as a hidden input, the source filename as another
# hidden input, and four submit buttons with ``formaction`` targeting
# the per-format routes. Tests cover each route's success path plus
# shared guarantees (filename shape, empty-findings tolerance).


_SAMPLE_FINDINGS = [
    {
        "rule_id": "M11_001",
        "severity": "error",
        "status": "Failed",
        "message": "Required missing.",
        "expected": "Text",
        "actual": "(no value)",
        "element_name": "Full Title",
        "section_number": "",
        "section_title": "Title Page",
    }
]


def _form_payload(findings=None, source="protocol.docx"):
    import json as _json

    return {
        "findings": _json.dumps(findings or []),
        "source_filename": source,
    }


@pytest.mark.anyio
async def test_download_csv_returns_plain_csv(monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        "/validate/m11-docx/download/csv",
        data=_form_payload(_SAMPLE_FINDINGS),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    disp = response.headers["content-disposition"]
    assert "protocol-m11-findings-" in disp
    assert disp.endswith('.csv"')
    body = response.content.decode("utf-8")
    # Header row + one data row. Fields are in the fixed formatter
    # order — not load-bearing for the test but nice to spot-check.
    assert "rule_id,severity,status,element_name" in body
    assert "M11_001" in body
    assert "Full Title" in body


@pytest.mark.anyio
async def test_download_json_returns_findings_array(monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        "/validate/m11-docx/download/json",
        data=_form_payload(_SAMPLE_FINDINGS),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    import json as _json

    parsed = _json.loads(response.content.decode("utf-8"))
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["rule_id"] == "M11_001"


@pytest.mark.anyio
async def test_download_markdown_returns_heading_and_table(monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        "/validate/m11-docx/download/md",
        data=_form_payload(_SAMPLE_FINDINGS),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    body = response.content.decode("utf-8")
    assert body.startswith("# M11 Validation Findings")
    assert "| Rule | Severity" in body
    assert "| M11_001 |" in body


@pytest.mark.anyio
async def test_download_xlsx_returns_workbook(monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        "/validate/m11-docx/download/xlsx",
        data=_form_payload(_SAMPLE_FINDINGS),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    disp = response.headers["content-disposition"]
    assert "protocol-m11-findings-" in disp
    assert disp.endswith('.xlsx"')
    # An .xlsx is a zip — starts with PK header bytes.
    assert response.content[:2] == b"PK"


@pytest.mark.anyio
@pytest.mark.parametrize("fmt,content_marker", [
    ("csv", b"rule_id,severity"),
    ("json", b"[]"),
    ("md", b"_No findings._"),
    ("xlsx", b"PK"),
])
async def test_download_empty_findings_is_valid(monkeypatch, fmt, content_marker):
    """Zero findings is a normal case — every route must return a
    valid-but-empty file rather than erroring. Marker bytes vary per
    format but each proves the file is structurally sound."""
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        f"/validate/m11-docx/download/{fmt}",
        data=_form_payload(findings=[]),
    )
    assert response.status_code == 200
    assert content_marker in response.content


@pytest.mark.anyio
async def test_download_malformed_findings_json_degrades_to_empty(monkeypatch):
    """A malformed findings payload shouldn't 500 the route — the
    parser should swallow the JSON error and produce an empty file."""
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        "/validate/m11-docx/download/json",
        data={
            "findings": "this is not json",
            "source_filename": "protocol.docx",
        },
    )
    assert response.status_code == 200
    assert response.content.decode("utf-8").strip() == "[]"
