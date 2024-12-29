from app.usdm.fhir.factory.organization_factory import OrganizationFactory
from usdm_model.organization import Organization
from collections import OrderedDict

def test_organization():
  org = {
    "id": "Org_1", 
    "name": "ClinicalTrials.gov", 
    "label": "", 
    "type": {"id": "Code_1", "code": "C93453", "codeSystem": "http://www.cdisc.org", "codeSystemVersion": "2023-12-15", "decode": "Study Registry", "instanceType": "Code"},
    "identifierScheme": "USGOV", "identifier": "CT-GOV",
    "legalAddress": {
      "id": "Addr_1", "text": "line, city, district, state, postal_code, Denmark", "lines": ["line"], "city": "city", "district": "district", "state": "state", "postalCode": "postal_code",
      "country": {"id": "Code_2", "code": "DNK", "codeSystem": "ISO 3166 1 alpha3", "codeSystemVersion": "2020-08", "decode": "Denmark", "instanceType": "Code"},
      "instanceType": "Address"},
    "managedSites": [],
    "instanceType": "Organization"
  }
  org = Organization(**org)
  expected = _expected()
  result = OrganizationFactory(org)
  assert result.item is not None
  result_dict = to_dict(result.item)
  expected['id'] = result_dict['id']
  assert result_dict == expected

def test_organization_error(mocker, monkeypatch):
  result = OrganizationFactory(None)
  assert result.item is None

def to_dict(item):
  return _to_dict(dict(item))

def _to_dict(x):
  if isinstance(x, list):
    result = []
    for v in x:
      result.append(_to_dict(v))
    return result
  elif isinstance(x, dict):
    result = {}
    for k, v in x.items():
      result[k] = _to_dict(v)
    return result
  elif isinstance(x, str) or x is None:
    return x
  else:
    return _to_dict(dict(x))
  
def _expected():
  return {
    'resource_type': 'Organization',
    'fhir_comments': None,
    'id': '0fe821f3-4fbe-4946-9d3e-9630c1cbaf0c',
    'implicitRules': None,
    'implicitRules__ext': None,
    'language': None,
    'language__ext': None,
    'meta': None,
    'contained': None,
    'extension': None,
    'modifierExtension': None,
    'text': None,
    'active': None,
    'active__ext': None,
    'alias': None,
    'alias__ext': None,
    'contact': [
      {
        'resource_type': 'ExtendedContactDetail',
        'fhir_comments': None,
        'extension': None,
        'id': None,
        'address': {
          'resource_type': 'Address',
          'fhir_comments': None,
          'extension': None,
          'id': 'Addr_1',
          'city': 'city',
          'city__ext': None,
          'country': 'Denmark',
          'country__ext': None,
          'district': 'district',
          'district__ext': None,
          'line': None,
          'line__ext': None,
          'period': None,
          'postalCode': 'postal_code',
          'postalCode__ext': None,
          'state': 'state',
          'state__ext': None,
          'text': 'line, city, district, state, postal_code, Denmark',
          'text__ext': None,
          'type': None,
          'type__ext': None,
          'use': None,
          'use__ext': None
        },
        'name': None,
        'organization': None,
        'period': None,
        'purpose': None,
        'telecom': None
      }
    ],
    'description': None,
    'description__ext': None,
    'endpoint': None,
    'identifier': None,
    'name': 'ClinicalTrials.gov',
    'name__ext': None,
    'partOf': None,
    'qualification': None,
    'type': None
  }