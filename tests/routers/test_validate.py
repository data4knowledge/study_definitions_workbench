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
    """POST runs M11Validator against the stored DOCX and renders the
    findings table. The annotated-protocol view was removed from this
    flow in task #36 — the route now only projects findings and passes
    download metadata to the results partial."""
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

    # Validator runs standalone against the stored docx path — no
    # Wrapper involvement.  Mock count() > 0 so the route takes the
    # happy path and doesn't emit the "extraction failed" message.
    validator_cls = mocker.patch("app.routers.validate.M11Validator")
    validator_instance = validator_cls.return_value
    results_mock = MagicMock()
    results_mock.count.return_value = 1
    validator_instance.validate.return_value = results_mock

    # Stub the projection so we control the finding dicts exactly —
    # the template renders ``rule_id``, ``severity``, ``section``,
    # ``element``, and ``message`` for each row.
    mocker.patch(
        "app.routers.validate.project_m11_result",
        return_value=[
            {
                "rule_id": "M11_001",
                "severity": "error",
                "section": "Title Page",
                "element": "Full Title",
                "message": "Required element 'Full Title' is missing.",
                "rule_text": "",
                "path": "",
            }
        ],
    )

    response = await async_client.post("/validate/m11-docx")
    assert response.status_code == 200
    assert mock_called(uc)
    validator_instance.validate.assert_called_once()
    # Lock in the DataFiles convention: the route must use the existing
    # "docx" media_type. Inventing a new one (e.g. "m11") raises KeyError
    # from DataFiles.path — a hazard we already hit once.
    save_type = df_instance.save.call_args.args[0]
    path_type = df_instance.path.call_args.args[0]
    assert save_type == "docx"
    assert path_type == "docx"
    # Finding row rendered in the shared findings table.
    body = response.text
    assert "M11_001" in body
    assert "Full Title" in body
    # Jinja autoescape converts apostrophes to ``&#39;`` in HTML output —
    # the rendered cell carries the escaped form, not the raw string.
    assert "Required element &#39;Full Title&#39; is missing." in body
    # Annotated-document artifacts must not appear — task #36 stripped
    # the tab entirely from the standalone flow.
    assert "m11-doc-marker" not in body
    assert "m11-annotated-doc" not in body
    assert "data-m11-finding-index" not in body
    assert "Annotated document" not in body


@pytest.mark.anyio
async def test_validate_m11_docx_post_extraction_failure(mocker, monkeypatch):
    """When the validator couldn't even run (count==0 but the operational
    error log is non-empty), the route surfaces the "extraction failed"
    message instead of silently claiming success."""
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

    # Validator ran but produced no rule outcomes AND the operational
    # error log records a reader failure — the two-channel signal the
    # route watches for.  Patch the Errors instance the route creates so
    # count() reports at least one entry.
    validator_cls = mocker.patch("app.routers.validate.M11Validator")
    validator_cls.return_value.validate.return_value = MagicMock(count=lambda: 0)
    errors_cls = mocker.patch("app.routers.validate.M11Errors")
    errors_cls.return_value.count.return_value = 1

    response = await async_client.post("/validate/m11-docx")
    assert response.status_code == 200
    assert "Validation could not be completed" in response.text


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
        "section": "Title Page",
        "element": "Full Title",
        "message": "Required missing.",
        "rule_text": "",
        "path": "",
    }
]


def _form_payload(findings=None, source="protocol.docx"):
    import json as _json

    # ``kind`` is the validator tag that slots into the filename —
    # defaults to ``m11-findings`` here so filename assertions
    # (``…-m11-findings-YYYY-MM-DD.ext``) still hold after the
    # route rename. The USDM CORE / Rules flows pass their own
    # ``kind`` values at their own call sites.
    return {
        "findings": _json.dumps(findings or []),
        "source_filename": source,
        "kind": "m11-findings",
    }


@pytest.mark.anyio
async def test_download_csv_returns_plain_csv(monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        "/validate/download/csv",
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
    assert "rule_id,severity,section,element,message" in body
    assert "M11_001" in body
    assert "Full Title" in body


@pytest.mark.anyio
async def test_download_json_returns_findings_array(monkeypatch):
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        "/validate/download/json",
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
        "/validate/download/md",
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
        "/validate/download/xlsx",
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
@pytest.mark.parametrize(
    "fmt,content_marker",
    [
        ("csv", b"rule_id,severity"),
        ("json", b"[]"),
        ("md", b"_No findings._"),
        ("xlsx", b"PK"),
    ],
)
async def test_download_empty_findings_is_valid(monkeypatch, fmt, content_marker):
    """Zero findings is a normal case — every route must return a
    valid-but-empty file rather than erroring. Marker bytes vary per
    format but each proves the file is structurally sound."""
    protect_endpoint()
    async_client = mock_async_client(monkeypatch)
    response = await async_client.post(
        f"/validate/download/{fmt}",
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
        "/validate/download/json",
        data={
            "findings": "this is not json",
            "source_filename": "protocol.docx",
        },
    )
    assert response.status_code == 200
    assert response.content.decode("utf-8").strip() == "[]"
