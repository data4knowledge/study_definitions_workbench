from app.usdm.fhir.factory.label_type_factory import LabelTypeFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm_model.code import Code

def test_label_type():
  usdm_code_dict = {
    'code': 'code',
    'codeSystem': 'codesys',
    'codeSystemVersion': '3',
    'decode': 'USA',
    'id': 'Code1',
    'instanceType': 'Code'
  }
  code = Code(**usdm_code_dict)
  params = {'usdm_code': code, 'text': 'xxxxxxxxx'}
  expected = {
    'type': {
      'coding': [
          {
            'code': 'code',
            'code__ext': None,
            'display': 'USA',
            'display__ext': None,
            'extension': None,
            'fhir_comments': None,
            'id': None,
            'resource_type': 'Coding',
            'system': 'codesys',
            'system__ext': None,
            'userSelected': None,
            'userSelected__ext': None,
            'version': '3',
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
    'value': 'xxxxxxxxx',
  }
  result = LabelTypeFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_label_type_error(mocker, monkeypatch):
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = LabelTypeFactory(**params)
  assert result.item is None

