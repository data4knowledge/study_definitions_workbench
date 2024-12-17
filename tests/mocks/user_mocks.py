from tests.mocks.factory_mocks import factory_user, factory_user_2, factory_endpoint

def mock_user_endpoints_page(mocker):
  mock = mocker.patch("app.database.user.User.endpoints_page")
  mock.side_effect = [{'page': 1, 'size': 10, 'count': 0, 'filter': '', 'items': []}]
  return mock

def mock_user_valid(mocker):
  mock = mocker.patch("app.database.user.User.valid")
  mock.side_effect = [{'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}}]
  return mock

def mock_endpoint_valid(mocker):
  mock = mocker.patch("app.database.endpoint.Endpoint.valid")
  mock.side_effect = [{'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''},}]
  return mock

def mock_user_update_display_name(mocker):
  mock = mocker.patch("app.database.user.User.update_display_name")
  mock.side_effect = [(factory_user_2(), {'display_name': {'valid': True, 'message': ''}, 'email': {'valid': True, 'message': ''}, 'identifier': {'valid': True, 'message': ''}})]
  return mock

def mock_endpoint_create(mocker):
  mock = mocker.patch("app.database.endpoint.Endpoint.create")
  mock.side_effect = [(factory_endpoint(),  {'name': {'valid': True, 'message': ''}, 'endpoint': {'valid': True, 'message': ''}, 'type': {'valid': True, 'message': ''}})]
  return mock

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
