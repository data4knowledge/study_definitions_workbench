from tests.mocks.factory_mocks import *

def mock_file_import_find(mocker):
  mock = mocker.patch("app.model.file_import.FileImport.find")
  mock.side_effect = [factory_file_import()]
  return mock