import pytest
from tests.mocks.general_mocks import *
from tests.mocks.user_mocks import *
from tests.mocks.fastapi_mocks import *
from tests.mocks.file_mocks import *

@pytest.fixture
def anyio_backend():
  return 'asyncio'

def test_study_select(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_exists(mocker)
  ss = mock_study_summary(mocker)
  response = client.patch(
    "/studies/15/select?action=select", 
    data={'list_studies': '1, 2'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """<input type="hidden" name="list_studies" id="list_studies" value="1,2,15">""" in response.text
  assert mock_called(ss)

def mock_study_summary(mocker):
  mock = mocker.patch("app.database.study.Study.summary")
  mock.side_effect = ["Study Summary"]
  return mock

def test_study_deselect(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  mock_user_check_exists(mocker)
  summary = mock_study_summary(mocker)
  summary.side_effect = ["Study Summary"]
  response = client.patch(
    "/studies/15/select?action=deselect", 
    data={'list_studies': '1, 2,15'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  assert response.status_code == 200
  assert """<input type="hidden" name="list_studies" id="list_studies" value="1,2">""" in response.text

def test_study_delete(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  sf = mock_study_find(mocker)
  sfi = mock_study_file_imports(mocker)
  dfd = mock_data_file_delete(mocker)
  fif = mock_file_import_find(mocker)
  fid = mock_file_import_delete(mocker)
  sd = mock_study_delete(mocker)
  response = client.post(
    "/studies/delete", 
    data={'delete_studies': '1'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    follow_redirects=False
  )
  assert response.status_code == 303
  assert str(response.next_request.url) == "http://testserver/index"
  assert mock_called(sf)
  assert mock_called(sfi)
  assert mock_called(fif)
  assert mock_called(fid)
  assert mock_called(dfd)
  assert mock_called(sd)

def mock_study_file_imports(mocker):
  mock = mocker.patch("app.database.study.Study.file_imports")
  mock.side_effect = [[[12,'1234-5678']]]
  return mock

def mock_study_delete(mocker):
  mock = mocker.patch("app.database.study.Study.delete")
  mock.side_effect = [1]
  return mock

def mock_study_find(mocker):
  mock = mocker.patch("app.database.study.Study.find")
  mock.side_effect = [factory_study()]
  return mock

def test_file_list_local(mocker, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  uc = mock_user_check_exists(mocker)
  fp = mock_file_picker_os(mocker)
  lfd = mock_local_files_dir(mocker)
  response = client.get("/fileList?dir=xxx&url=http://example.com")
  assert response.status_code == 200
  assert """<p class="card-text">a-file.txt</p>""" in response.text
  assert """<p class="card-text">100 kb</p>""" in response.text
  assert mock_called(uc)
  assert mock_called(fp)
  assert mock_called(lfd)

def test_file_list_local_invalid(mocker, caplog, monkeypatch):
  protect_endpoint()
  client = mock_client(monkeypatch)
  uc = mock_user_check_exists(mocker)
  fp = mock_file_picker_os(mocker)
  lfd = mock_local_files_dir_error(mocker)
  response = client.get("/fileList?dir=xxx&url=http://example.com")
  assert response.status_code == 200
  assert """Error Error Error!!!""" in response.text
  assert mock_called(uc)
  assert mock_called(fp)
  assert mock_called(lfd)
  assert error_logged(caplog, "Error Error Error!!!")
