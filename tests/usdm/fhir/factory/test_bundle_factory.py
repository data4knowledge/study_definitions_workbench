from datetime import datetime, date
from zoneinfo import ZoneInfo
from app.usdm.fhir.factory.bundle_factory import BundleFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from fhir.resources.identifier import Identifier

def test_bundle():
  date_obj = datetime(2024, 12, 31, 0, 0, tzinfo=ZoneInfo(key='Europe/Amsterdam'))
  date_str = date_obj.isoformat()
  print(f"DATE: {date_str}")
  identifier = Identifier(system='urn:ietf:rfc:3986', value=f'urn:uuid:1234-5678')
  params = {'entry': [], 'type': 'document', 'identifier': identifier, 'timestamp': date_str}
  expected = {
    'entry': [],
    'fhir_comments': None,
    'id': None,
    'identifier': {
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
        'value': 'urn:uuid:1234-5678',
        'value__ext': None,
    },
    'implicitRules': None,
    'implicitRules__ext': None,
    'issues': None,
    'language': None,
    'language__ext': None,
    'link': None,
    'meta': None,
    'resource_type': 'Bundle',
    'signature': None,
    'timestamp': '2024-12-31 00:00:00+01:00',
    'timestamp__ext': None,
    'total': None,
    'total__ext': None,
    'type': 'document',
    'type__ext': None,
}
  result = BundleFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_extension_error(mocker, monkeypatch):
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = BundleFactory(**params)
  assert result.item is None
