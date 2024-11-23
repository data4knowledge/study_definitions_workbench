def mock_post(mocker, path='d4kms_generic.service.Service'):
  mock = mocker.patch(f"{path}.post")
  mock.side_effect = [{'address': 'address'}]
  return mock
