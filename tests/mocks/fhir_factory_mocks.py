def mock_handle_exception(mocker):
  mock = mocker.patch("app.usdm.fhir.factory.base_factory.BaseFactory.handle_exception")
  return mock