import pytest
import datetime
from app.database.user import User
from app.database.study import Study
from app.database.version import Version
from app.database.file_import import FileImport
from app.database.endpoint import Endpoint
from app.configuration.configuration import application_configuration
from tests.mocks.fastapi_mocks import *
from tests.mocks.usdm_json_mocks import *
from tests.mocks.file_mocks import *
from tests.mocks.general_mocks import *


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
    assert """Our privacy policy can be downloaded from""" in response.text


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
    assert """Our privacy policy can be downloaded from""" not in response.text


@pytest.mark.anyio
async def test_login_single(monkeypatch):
    async_client = mock_async_client(monkeypatch)
    monkeypatch.setenv("SINGLE_USER", "True")
    response = await async_client.get("/login")
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
    assert str(response.next_request.url).startswith("https://dev-0")


def mock_user_check_exists(mocker):
    uc = mock_user_check(mocker)
    uc.side_effect = [(factory_user(), True)]
    return uc


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


def factory_file_import() -> FileImport:
    return FileImport(
        **{
            "filepath": "filepath",
            "filename": "filename",
            "type": "XXX",
            "status": "Done",
            "uuid": "1234-5678",
            "id": 1,
            "user_id": 1,
            "created": datetime.datetime.now(),
        }
    )


def factory_endpoint() -> FileImport:
    return Endpoint(
        **{
            "name": "Endpoint One",
            "endpoint": "http://example.com",
            "type": "XXX",
            "id": 1,
        }
    )
