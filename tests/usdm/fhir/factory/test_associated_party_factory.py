from app.usdm.fhir.factory.associated_party_factory import AssociatedPartyFactory
from tests.usdm.fhir.factory.dict_result import DictResult

def test_associated_party_display():
  params = {'role_code': 'xxx', 'role_display': 'yyy', 'party': {'display': '1234'}}
  expected = {
    'modifierExtension': None,
    'classifier': None,
    'name': None,
    'name__ext': None,
    'period': None,
    'party': {
      'display': '1234',
      'display__ext': None,
      'extension': None,
      'fhir_comments': None,
      'id': None,
      'resource_type': 'Reference',
      'identifier': None,
      'reference': None,
      'reference__ext': None,
      'type': None,
      'type__ext': None
    },
    'resource_type': 'ResearchStudyAssociatedParty',
    'role': {
      'coding': [
          {
            'code': 'xxx',
            'code__ext': None,
            'display': 'yyy',
            'display__ext': None,
            'extension': None,
            'fhir_comments': None,
            'id': None,
            'resource_type': 'Coding',
            'system': 'http://hl7.org/fhir/research-study-party-role',
            'system__ext': None,
            'userSelected': None,
            'userSelected__ext': None,
            'version': None,
            'version__ext': None,
          },
      ],
      'extension': None,
      'fhir_comments': None,
      'id': None,
      'resource_type': 'CodeableConcept',
      'text': None,
      'text__ext': None
    },
    'extension': None,
    'fhir_comments': None,
    'id': None,
  }
  result = AssociatedPartyFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_associated_party_reference():
  params = {'role_code': 'xxx', 'role_display': 'yyy', 'party': {'reference': '1234'}}
  expected = {
    'modifierExtension': None,
    'classifier': None,
    'name': None,
    'name__ext': None,
    'period': None,
    'party': {
      'display': None,
      'display__ext': None,
      'extension': None,
      'fhir_comments': None,
      'id': None,
      'resource_type': 'Reference',
      'identifier': None,
      'reference': '1234',
      'reference__ext': None,
      'type': None,
      'type__ext': None
    },
    'resource_type': 'ResearchStudyAssociatedParty',
    'role': {
      'coding': [
          {
            'code': 'xxx',
            'code__ext': None,
            'display': 'yyy',
            'display__ext': None,
            'extension': None,
            'fhir_comments': None,
            'id': None,
            'resource_type': 'Coding',
            'system': 'http://hl7.org/fhir/research-study-party-role',
            'system__ext': None,
            'userSelected': None,
            'userSelected__ext': None,
            'version': None,
            'version__ext': None,
          },
      ],
      'extension': None,
      'fhir_comments': None,
      'id': None,
      'resource_type': 'CodeableConcept',
      'text': None,
      'text__ext': None
    },
    'extension': None,
    'fhir_comments': None,
    'id': None,
  }
  result = AssociatedPartyFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_associated_party_error(mocker, monkeypatch):
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = AssociatedPartyFactory(**params)
  assert result.item is None

