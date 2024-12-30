from app.usdm.fhir.factory.progress_status_factory import ProgressStatusFactory
from tests.usdm.fhir.factory.dict_result import DictResult

def test_progress_status():
  params = {'state_code': 'xxx', 'state_display': 'yyy', 'value': '1234'}
  expected = {
    'modifierExtension': None,
    'actual': None,
    'actual__ext': None,
    'period': {
      'end': None,
      'end__ext': None,
      'extension': None,
      'fhir_comments': None,
      'id': None,
      'resource_type': 'Period',
      'start': '1234',
      'start__ext': None,
    },
    'resource_type': 'ResearchStudyProgressStatus',
    'state': {
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
  result = ProgressStatusFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_codeable_concept_error(mocker, monkeypatch):
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = ProgressStatusFactory(**params)
  assert result.item is None

