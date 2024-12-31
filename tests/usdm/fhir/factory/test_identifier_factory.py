from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm_model.code import Code

def test_identifier():
  params = {'system': 'urn:ietf:rfc:3986', 'value': f'urn:uuid:1234-5678.91011'}
  expected = {
    'assigner': None,
    'extension': None,
    'fhir_comments': None,
    'id': None,
    'period': None,
    'resource_type': 'Identifier',
    'system': 'urn:ietf:rfc:3986',
    'system__ext': None,
    'type': None,
    'use': None,
    'use__ext': None,
    'value': 'urn:uuid:1234-5678.91011',
    'value__ext': None,
  }
  result = IdentifierFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_label_type_error(mocker, monkeypatch):
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = IdentifierFactory(**params)
  assert result.item is None

