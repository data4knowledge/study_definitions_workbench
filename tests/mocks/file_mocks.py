from tests.mocks.factory_mocks import *

def mock_file_import_find(mocker):
  mock = mocker.patch("app.model.file_import.FileImport.find")
  mock.side_effect = [factory_file_import()]
  return mock

def mock_file_import_delete(mocker):
  mock = mocker.patch("app.model.file_import.FileImport.delete")
  mock.side_effect = [1]
  return mock

def mock_data_file_delete(mocker):
  mock = mocker.patch("app.model.file_handling.data_files.DataFiles.delete")
  mock.side_effect = [1]
  return mock

def mock_file_picker_os(mocker):
  fp = mocker.patch("app.main.file_picker")
  fp.side_effect = [{'browser': False, 'os': True, 'pfda': False, 'source': 'os'}]
  return fp

def mock_local_files_dir(mocker):
  lfd = mocker.patch("app.model.file_handling.local_files.LocalFiles.dir")
  ts = datetime.datetime.now()
  files = [{'uid': 1234-5678, 'type': 'File', 'name': 'a-file.txt', 'path': 'xxx/a-file.txt', 'created_at': ts, 'file_size': '100 kb'}]
  lfd.side_effect = [(True, {'files': files, 'dir': 'xxx'}, '')]
  return lfd

def mock_local_files_dir_error(mocker):
  mock = mocker.patch("app.model.file_handling.local_files.LocalFiles.dir")
  files = []
  mock.side_effect = [(False, {'files': files, 'dir': 'xxx'}, 'Error Error Error!!!')]
  return mock
