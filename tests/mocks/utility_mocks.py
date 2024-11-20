
# def mock_single_user_true(mocker):
#   mock = mocker.patch("app.dependencies.utility.single_user")
#   mock.side_effect = [True]
#   return mock

# def mock_single_user_false(mocker):
#   mock = mocker.patch("app.dependencies.utility.single_user")
#   mock.side_effect = [False]
#   return mock

# def mock_is_admin_true(mocker):
#   mock = mocker.patch("app.dependencies.utility.is_admin")
#   mock.side_effect = [True]
#   return mock

# def mock_is_admin_false(mocker):
#   mock = mocker.patch("app.dependencies.utility.is_admin")
#   mock.side_effect = [False]
#   return mock

def mock_is_fhir_tx_true(mocker, path='app.routers.transmissions'):
  # The path below could ne made configurable
  mock = mocker.patch(f"{path}.is_fhir_tx")
  print(f"MOCK: {mock}")
  mock.side_effect = [True]
  return mock

def mock_is_fhir_tx_false(mocker, path='app.routers.transmissions'):
  # The path below could ne made configurable
  mock = mocker.patch(f"{path}.is_fhir_tx")
  mock.side_effect = [False]
  return mock
