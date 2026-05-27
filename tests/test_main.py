import pytest
from unittest.mock import MagicMock, AsyncMock
from app.database.user import User
from app.database.study import Study
from app.database.version import Version
from app.database.file_import import FileImport
from app.database.endpoint import Endpoint
from app.configuration.configuration import application_configuration
from tests.mocks.fastapi_mocks import (
    mock_client,
    mock_client_multiple,
    mock_async_client,
    protect_endpoint,
)
from tests.mocks.user_mocks import mock_user_check_exists
from tests.mocks.usdm_json_mocks import mock_usdm_json_init, mock_usdm_study_version
# from tests.mocks.usdm_json_mocks import mock_usdm_json_init, mock_usdm_json_timelines
# from tests.mocks.file_mocks import mock_file_import_find, mock_file_import_delete, mock_data_file_delete, mock_local_files_dir, mock_local_files_dir_error


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_home(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    client = mock_client(monkeypatch)
    response = client.get("/")
    assert response.status_code == 200
    assert (
        """style="background-image: url('static/images/background.jpg'); height: 100vh">"""
        in response.text
    )
    assert """Welcome to the d4k Study Definitions Workbench""" in response.text
    assert """Our privacy policy can be viewed""" in response.text


def test_home_single(mocker, monkeypatch):
    application_configuration.single_user = True
    application_configuration.multiple_user = False
    client = mock_client(monkeypatch)
    response = client.get("/")
    assert response.status_code == 200
    assert (
        """style="background-image: url('static/images/background.jpg'); height: 100vh">"""
        in response.text
    )
    assert """Welcome to the d4k Study Definitions Workbench""" in response.text
    assert """Our privacy policy can be viewed""" not in response.text


@pytest.mark.anyio
async def test_login_single(monkeypatch):
    async_client = mock_async_client(monkeypatch)
    monkeypatch.setenv("SINGLE_USER", "True")
    response = await async_client.get("/login")
    assert response.status_code == 307
    assert str(response.next_request.url) == "http://test/index"


@pytest.mark.anyio
async def test_register_single(monkeypatch):
    async_client = mock_async_client(monkeypatch)
    monkeypatch.setenv("SINGLE_USER", "True")
    application_configuration.single_user = True
    response = await async_client.get("/register")
    assert response.status_code == 307
    assert str(response.next_request.url) == "http://test/index"


# def test_import_m11(mocker, monkeypatch):
#     protect_endpoint()
#     client = mock_client(monkeypatch)
#     uc = mock_user_check_exists(mocker)
#     application_configuration.file_picker = {
#         "browser": False,
#         "os": True,
#         "pfda": False,
#         "source": "os",
#     }
#     response = client.get("/import/m11")
#     assert response.status_code == 200
#     assert '<h4 class="card-title">Import M11 Protocol</h4>' in response.text
#     assert """<p>Select a single M11 file</p>""" in response.text
#     assert mock_called(uc)


# def test_import_xl(mocker, monkeypatch):
#     protect_endpoint()
#     client = mock_client(monkeypatch)
#     uc = mock_user_check_exists(mocker)
#     application_configuration.file_picker = {
#         "browser": False,
#         "os": True,
#         "pfda": False,
#         "source": "os",
#     }
#     response = client.get("/import/xl")
#     assert response.status_code == 200
#     assert '<h4 class="card-title">Import USDM Excel Definition</h4>' in response.text
#     assert (
#         "<p>Select a single Excel file and zero, one or more images files. </p>"
#         in response.text
#     )
#     assert mock_called(uc)


# @pytest.mark.anyio
# async def test_import_m11_execute(mocker, monkeypatch):
#     protect_endpoint()
#     async_client = mock_async_client(monkeypatch)
#     uc = mock_user_check_exists(mocker)
#     pm11 = mock_process_m11(mocker)
#     response = await async_client.post("/import/m11")
#     assert response.status_code == 200
#     assert "<h1>Fake M11 Response</h1>" in response.text
#     assert mock_called(uc)
#     assert mock_called(pm11)


# def mock_process_m11(mocker):
#     mock = mocker.patch("app.main.process_m11")
#     mock.side_effect = ["<h1>Fake M11 Response</h1>"]
#     return mock


# @pytest.mark.anyio
# async def test_import_xl_execute(mocker, monkeypatch):
#     protect_endpoint()
#     async_client = mock_async_client(monkeypatch)
#     uc = mock_user_check_exists(mocker)
#     pxl = mock_process_xl(mocker)
#     response = await async_client.post("/import/xl")
#     assert response.status_code == 200
#     assert "<h1>Fake XL Response</h1>" in response.text
#     assert mock_called(uc)
#     assert mock_called(pxl)


# def mock_process_xl(mocker):
#     mock = mocker.patch("app.main.process_xl")
#     mock.side_effect = ["<h1>Fake XL Response</h1>"]
#     return mock


# def test_import_status(mocker, monkeypatch):
#     protect_endpoint()
#     client = mock_client(monkeypatch)
#     uc = mock_user_check_exists(mocker)
#     response = client.get("/import/status?page=1&size=10&filter=")
#     assert response.status_code == 200
#     assert '<h5 class="card-title">Import Status</h5>' in response.text
#     assert mock_called(uc)


# def test_import_status_data(mocker, monkeypatch):
#     protect_endpoint()
#     client = mock_client(monkeypatch)
#     uc = mock_user_check_exists(mocker)
#     fip = mock_file_import_page(mocker)
#     response = client.get("/import/status/data?page=1&size=10&filter=")
#     assert response.status_code == 200
#     assert '<div id="data_div">' in response.text
#     assert '<th scope="col">Imported At</th>' in response.text
#     assert mock_called(uc)
#     assert mock_called(fip)


# def mock_file_import_page(mocker):
#     mock = mocker.patch("app.database.file_import.FileImport.page")
#     mock.side_effect = [{"page": 1, "size": 10, "count": 0, "filter": "", "items": []}]
#     return mock


# def test_import_errors(mocker, monkeypatch):
#     protect_endpoint()
#     client = mock_client(monkeypatch)
#     uc = mock_user_check_exists(mocker)
#     fif = mock_file_import_find(mocker)
#     dfp = mock_data_file_path(mocker)
#     response = client.get("/import/1/errors")
#     assert response.status_code == 200
#     assert "Test File" in response.text
#     assert mock_called(uc)
#     assert mock_called(fif)
#     assert mock_called(dfp)


# def test_import_errors_error(mocker, monkeypatch):
#     protect_endpoint()
#     client = mock_client(monkeypatch)
#     uc = mock_user_check_exists(mocker)
#     fif = mock_file_import_find(mocker)
#     dfp = mock_data_file_path_error(mocker)
#     response = client.get("/import/1/errors")
#     assert response.status_code == 200
#     assert '<p class="lead text-danger">Fatal Error</p>' in response.text
#     assert (
#         "<p>Something went wrong downloading the errors file for the import</p>"
#         in response.text
#     )
#     assert mock_called(uc)
#     assert mock_called(fif)
#     assert mock_called(dfp)


# def mock_file_import_find(mocker):
#     mock = mocker.patch("app.database.file_import.FileImport.find")
#     mock.side_effect = [factory_file_import()]
#     return mock


# def mock_data_file_path(mocker):
#     mock = mocker.patch("app.model.file_handling.data_files.DataFiles.path")
#     mock.side_effect = [("tests/test_files/main/simple.txt", "simple.txt", True)]
#     return mock


# def mock_data_file_path_error(mocker):
#     mock = mocker.patch("app.model.file_handling.data_files.DataFiles.path")
#     mock.side_effect = [("", "", False)]
#     return mock


# def test_get_study_design_timelines(mocker, monkeypatch):
#   protect_endpoint()
#   client = mock_client(monkeypatch)
#   uji = mock_usdm_json_init(mocker)
#   ujt = mock_usdm_json_timelines(mocker)
#   response = client.get("/versions/1/studyDesigns/1/timelines")
#   assert response.status_code == 200
#   #print(f"RESULT: {response.text}")
#   assert '<a href="/versions/1/studyDesigns/2/timelines/3/soa" class="btn btn-sm btn-outline-primary rounded-5">' in response.text
#   assert 'Special Timeline' in response.text
#   assert mock_called(uji)
#   assert mock_called(ujt)

# def test_get_study_design_soa(mocker, monkeypatch):
#   protect_endpoint()
#   client = mock_client(monkeypatch)
#   uji = mock_usdm_json_init(mocker)
#   ujs = mock_usdm_json_soa(mocker)
#   response = client.get("/versions/1/studyDesigns/2/timelines/3/soa")
#   assert response.status_code == 200
#   #print(f"RESULT: {response.text}")
#   assert '<h5 class="card-title">Schedule of Activities: SOA LABEL</h5>' in response.text
#   assert '<h6 class="card-subtitle mb-2 text-muted">Description: SOA Description | Main: False | Name: SoA Name</h6>' in response.text
#   assert mock_called(uji)
#   assert mock_called(ujs)


def test_get_logout_single(mocker, monkeypatch):
    application_configuration.single_user = True
    application_configuration.multiple_user = False
    client = mock_client(monkeypatch)
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 307
    assert str(response.next_request.url) == "http://testserver/"


def test_get_logout_multiple(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    client = mock_client_multiple(mocker)
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 307
    assert str(response.next_request.url) == "http://testserver/"


# def mock_user_check_exists(mocker):
#     uc = mock_user_check(mocker)
#     uc.side_effect = [(factory_user(), True)]
#     return uc


def mock_user_check_new(mocker):
    uc = mock_user_check(mocker)
    uc.side_effect = [(factory_user(), False)]
    return uc


def mock_user_check_fail(mocker):
    uc = mock_user_check(mocker)
    uc.side_effect = [(None, False)]
    return uc


def mock_user_find(mocker):
    uf = mocker.patch("app.database.user.User.find")
    uf.side_effect = [factory_user()]
    return uf


def mock_user_check(mocker):
    return mocker.patch("app.database.user.User.check")


def factory_user() -> User:
    return User(
        **{
            "identifier": "FRED",
            "email": "fred@example.com",
            "display_name": "Fred Smith",
            "is_active": True,
            "id": 1,
        }
    )


def factory_user_2() -> User:
    return User(
        **{
            "identifier": "FRED",
            "email": "fred@example.com",
            "display_name": "Fred Smithy",
            "is_active": True,
            "id": 1,
        }
    )


def factory_study() -> Study:
    return Study(
        **{
            "name": "STUDYNAME",
            "title": "Study Title",
            "phase": "Phase 1",
            "sponsor": "ACME",
            "sponsor_identifier": "STUDY IDENTIFIER",
            "nct_identifier": "NCT12345678",
            "id": 1,
            "user_id": 1,
        }
    )


def factory_version() -> Version:
    return Version(**{"version": "1", "id": 1, "import_id": 1, "study_id": 1})


# def factory_file_import() -> FileImport:
#     return FileImport(
#         **{
#             "filepath": "filepath",
#             "filename": "filename",
#             "type": "XXX",
#             "status": "Done",
#             "uuid": "1234-5678",
#             "id": 1,
#             "user_id": 1,
#             "created": datetime.datetime.now(),
#         }
#     )


def factory_endpoint() -> FileImport:
    return Endpoint(
        **{
            "name": "Endpoint One",
            "endpoint": "http://example.com",
            "type": "XXX",
            "id": 1,
        }
    )


def _mock_usdm_init_with_attrs(mocker, path="app.main"):
    """Mock USDMJson.__init__ setting commonly accessed attributes."""

    def custom_init(self, *args, **kwargs):
        self.id = args[0] if args else 1
        self.m11 = True
        self.uuid = "test-uuid"
        self._files = MagicMock()

    mocker.patch(f"{path}.USDMJson.__init__", new=custom_init)


# --- Study design routes ---


def test_study_design_summary(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    _mock_usdm_init_with_attrs(mocker)
    response = client.get("/versions/1/studyDesigns/design-1/summary")
    assert response.status_code == 200


def test_study_design_overall_parameters(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.study_design_overall_parameters",
        return_value={"id": 1, "m11": True, "text": "Test"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/overallParameters")
    assert response.status_code == 200


def test_study_design_design_parameters(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.study_design_design_parameters",
        return_value={"id": 1, "m11": True, "arms": 2},
    )
    response = client.get("/versions/1/studyDesigns/design-1/designParameters")
    assert response.status_code == 200


def test_study_design_schema(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.study_design_schema",
        return_value={"id": 1, "m11": True, "image": "", "text": "Schema"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/schema")
    assert response.status_code == 200


def test_study_design_interventions(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.study_design_interventions",
        return_value={"id": 1, "m11": True, "interventions": [], "text": "Test"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/interventions")
    assert response.status_code == 200


def test_study_design_estimands(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.study_design_estimands",
        return_value={"id": 1, "m11": True, "estimands": [], "text": "Test"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/estimands")
    assert response.status_code == 200


def test_study_design_ae_special_interest(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.adverse_events_special_interest",
        return_value={"id": 1, "m11": True, "text": "AE"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/aeSpecialInterest")
    assert response.status_code == 200


def test_study_design_safety_assessments(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.safety_assessments",
        return_value={"id": 1, "m11": True, "text": "Safety"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/safetyAssessments")
    assert response.status_code == 200


def test_study_design_sample_size(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.sample_size",
        return_value={"id": 1, "m11": True, "text": "100"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/sampleSize")
    assert response.status_code == 200


def test_study_design_analysis_sets(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.analysis_sets",
        return_value={"id": 1, "m11": True, "text": "Sets"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/analysisSets")
    assert response.status_code == 200


def test_study_design_analysis_objective(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.analysis_objectives",
        return_value={"id": 1, "m11": True, "text": "Obj"},
    )
    response = client.get("/versions/1/studyDesigns/design-1/analysisObjective")
    assert response.status_code == 200


# --- Safety / Statistics routes ---


def test_study_design_safety(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    _mock_usdm_init_with_attrs(mocker)
    response = client.get("/versions/1/studyDesigns/design-1/safety")
    assert response.status_code == 200


def test_study_design_statistics(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    _mock_usdm_init_with_attrs(mocker)
    response = client.get("/versions/1/studyDesigns/design-1/statistics")
    assert response.status_code == 200


def test_version_safety(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mock_usdm_study_version(mocker)
    response = client.get("/versions/1/safety")
    assert response.status_code == 200


def test_version_statistics(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mock_usdm_study_version(mocker)
    response = client.get("/versions/1/statistics")
    assert response.status_code == 200


# --- USDM views ---


def test_usdm_view(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mock_usdm_study_version(mocker)
    mocker.patch("app.main.USDMJson._get_raw", return_value='{"test": true}')
    response = client.get("/versions/1/usdm")
    assert response.status_code == 200


# --- Export routes ---


def test_export_fhir_success(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.fhir",
        return_value=("tests/test_files/main/simple.txt", "simple.txt", "text/plain"),
    )
    response = client.get("/versions/1/export/fhir?version=prism2")
    assert response.status_code == 200


def test_export_fhir_no_file(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch("app.main.USDMJson.fhir", return_value=("", "file.txt", "text/plain"))
    response = client.get("/versions/1/export/fhir?version=prism2")
    assert response.status_code == 200
    assert "Error" in response.text


def test_export_fhir_invalid_version(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    response = client.get("/versions/1/export/fhir?version=invalid_version")
    assert response.status_code == 200
    assert "Invalid FHIR" in response.text


def test_export_json_success(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.json",
        return_value=(
            "tests/test_files/main/simple.txt",
            "simple.txt",
            "application/json",
        ),
    )
    response = client.get("/versions/1/export/json")
    assert response.status_code == 200


def test_export_json_no_file(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mocker.patch(
        "app.main.USDMJson.json", return_value=("", "file.json", "application/json")
    )
    response = client.get("/versions/1/export/json")
    assert response.status_code == 200
    assert "Error" in response.text


# --- Transmit ---


def test_version_transmit_valid(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.run_fhir_m11_transmit")
    response = client.get(
        "/versions/1/transmit/2?version=prism3", follow_redirects=False
    )
    assert response.status_code == 307


def test_version_transmit_invalid(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    response = client.get("/versions/1/transmit/2?version=bad_version")
    assert response.status_code == 200
    assert "Invalid FHIR" in response.text


# --- Admin routes ---


def test_database_clean_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.admin_role_enabled", return_value=True)
    mocker.patch("app.main.DBM")
    mocker.patch("app.main.Endpoint.create", return_value=(MagicMock(), {}))
    response = client.get("/database/clean", follow_redirects=False)
    assert response.status_code == 307


def test_database_clean_not_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.admin_role_enabled", return_value=False)
    response = client.get("/database/clean", follow_redirects=False)
    assert response.status_code == 307


def test_database_debug_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.admin_role_enabled", return_value=True)
    mocker.patch("app.main.User.debug", return_value=[])
    mocker.patch("app.main.Study.debug", return_value=[])
    mocker.patch("app.main.Version.debug", return_value=[])
    mocker.patch("app.main.FileImport.debug", return_value=[])
    mocker.patch("app.main.Endpoint.debug", return_value=[])
    mocker.patch("app.main.UserEndpoint.debug", return_value=[])
    response = client.get("/database/debug")
    assert response.status_code == 200


def test_database_debug_not_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.admin_role_enabled", return_value=False)
    mocker.patch("app.main.connection_manager.error", new_callable=AsyncMock)
    response = client.get("/database/debug", follow_redirects=False)
    assert response.status_code == 303


def test_debug_level_debug(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.admin_role_enabled", return_value=True)
    response = client.patch("/debug?level=DEBUG")
    assert response.status_code == 200


def test_debug_level_info(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.admin_role_enabled", return_value=True)
    response = client.patch("/debug?level=INFO")
    assert response.status_code == 200


def test_debug_level_not_admin(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.admin_role_enabled", return_value=False)
    mocker.patch("app.main.connection_manager.error", new_callable=AsyncMock)
    response = client.patch("/debug?level=DEBUG")
    assert response.status_code == 200


# --- Callback ---


def test_login_multiple_shows_form(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    client = mock_client_multiple(mocker)
    response = client.get("/login")
    assert response.status_code == 200
    assert 'action="/login"' in response.text
    assert 'name="email"' in response.text


def test_login_submit_unknown_email(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    mocker.patch("app.main.User.find_by_email", return_value=None)
    client = mock_client_multiple(mocker)
    response = client.post("/login", data={"email": "nobody@example.com"})
    assert response.status_code == 200
    assert "Email not recognised" in response.text


def test_login_submit_known_email_sends_code(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    mocker.patch("app.main.User.find_by_email", return_value=MagicMock())
    gen = mocker.patch("app.main.generate_code", return_value="123456")
    send = mocker.patch("app.main.send_code_email", return_value=True)
    client = mock_client_multiple(mocker)
    response = client.post("/login", data={"email": "user@example.com"})
    assert response.status_code == 200
    assert 'action="/verify"' in response.text
    assert gen.called
    assert send.called


def test_verify_invalid_code(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    mocker.patch("app.main.verify_code", return_value=False)
    client = mock_client_multiple(mocker)
    response = client.post(
        "/verify", data={"email": "user@example.com", "code": "000000"}
    )
    assert response.status_code == 200
    assert "Invalid or expired code" in response.text


def test_register_page_multiple(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    client = mock_client_multiple(mocker)
    response = client.get("/register")
    assert response.status_code == 200
    assert 'action="/register"' in response.text
    assert 'name="email"' in response.text
    assert 'name="name"' in response.text


def test_register_submit_creates_and_sends(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    mocker.patch(
        "app.main.User.register", return_value=(MagicMock(), User.valid(), False)
    )
    gen = mocker.patch("app.main.generate_code", return_value="123456")
    send = mocker.patch("app.main.send_code_email", return_value=True)
    notify = mocker.patch("app.main.send_registration_notification", return_value=True)
    client = mock_client_multiple(mocker)
    response = client.post(
        "/register", data={"email": "new@data4knowledge.dk", "name": "New Person"}
    )
    assert response.status_code == 200
    assert 'action="/verify"' in response.text
    assert gen.called and send.called
    # New registration notifies the configured address.
    assert notify.called


def test_register_existing_email_does_not_notify(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    mocker.patch(
        "app.main.User.register", return_value=(MagicMock(), User.valid(), True)
    )
    mocker.patch("app.main.generate_code", return_value="123456")
    mocker.patch("app.main.send_code_email", return_value=True)
    notify = mocker.patch("app.main.send_registration_notification", return_value=True)
    client = mock_client_multiple(mocker)
    response = client.post(
        "/register", data={"email": "dup@gmail.com", "name": "Dup"}
    )
    assert response.status_code == 200
    # Already-registered email must not trigger a notification.
    assert not notify.called


def test_register_submit_invalid_name(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    validation = {"display_name": {"valid": False, "message": "Bad name"}}
    mocker.patch("app.main.User.register", return_value=(None, validation, False))
    client = mock_client_multiple(mocker)
    response = client.post(
        "/register", data={"email": "new@gmail.com", "name": "Bad!@#"}
    )
    assert response.status_code == 200
    assert "Bad name" in response.text


def test_verify_success_sets_session(mocker, monkeypatch):
    application_configuration.single_user = False
    application_configuration.multiple_user = True
    mocker.patch("app.main.verify_code", return_value=True)
    user = MagicMock()
    user.session_info.return_value = {
        "sub": "user@example.com",
        "email": "user@example.com",
        "nickname": "User",
        "roles": [],
    }
    mocker.patch("app.main.User.find_by_email", return_value=user)
    client = mock_client_multiple(mocker)
    response = client.post(
        "/verify",
        data={"email": "user@example.com", "code": "123456"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert str(response.next_request.url) == "http://testserver/index"


# --- USDM Explore/Diff ---


def test_usdm_explore(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mock_usdm_json_init(mocker)
    mock_usdm_study_version(mocker)
    mock_version = MagicMock()
    mock_version.import_id = 1
    mocker.patch("app.main.Version.find", return_value=mock_version)
    mock_fi = MagicMock()
    mock_fi.uuid = "test-uuid"
    mocker.patch("app.main.FileImport.find", return_value=mock_fi)
    mock_df = mocker.patch("app.main.DataFiles")
    mock_df.return_value.path.return_value = (
        "tests/test_files/main/simple.txt",
        "simple.txt",
        True,
    )
    mock_ds = mocker.patch("app.main.DataStore")
    mock_ds_instance = MagicMock()
    mock_ds_instance._klasses = {"Wrapper": {}, "Study": {"data": "test"}}
    mock_ds.return_value = mock_ds_instance
    response = client.get("/versions/1/usdmExplore")
    assert response.status_code == 200


def test_usdm_diff(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    mock_user_check_exists(mocker)
    mocker.patch("app.main.USDMJson.__init__", return_value=None)
    mock_usdm_study_version(mocker)
    mocker.patch("app.main.USDMJson._get_raw", return_value='{"test": true}')
    response = client.get("/versions/1/usdmDiff?previous=2")
    assert response.status_code == 200
