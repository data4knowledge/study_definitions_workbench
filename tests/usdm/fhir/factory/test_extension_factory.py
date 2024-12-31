from app.usdm.fhir.factory.extension_factory import ExtensionFactory
from tests.usdm.fhir.factory.dict_result import DictResult

def test_extension_string():
  params = {'url': 'amendmentNumber', 'valueString': 'something'}
  expected = {}
  expected['url'] = 'amendmentNumber'
  expected['valueString'] = 'something'
  result = ExtensionFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_extension_boolean():
  params = {'url': 'http://example.com/something', 'valueBoolean': 'true'}
  expected = {}
  expected['url'] = 'http://example.com/something'
  expected['valueBoolean'] = True
  result = ExtensionFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_extension_error(mocker, monkeypatch):
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = ExtensionFactory(**params)
  assert result.item is None
