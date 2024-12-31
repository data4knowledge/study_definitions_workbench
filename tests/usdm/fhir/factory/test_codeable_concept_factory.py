from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from fhir.resources.coding import Coding
from tests.usdm.fhir.factory.dict_result import DictResult
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

def test_codeable_concept_coding():
  params = {'coding': [Coding(system='Code System', version='1', code='Code', display='Decode')]}
  expected = {
    'coding': [
      {
        'code': 'Code',
        'display': 'Decode',
        'system': 'Code System',
        'version': '1',
      },
    ],
  }
  result = CodeableConceptFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_codeable_concept_text():
  params = {'text': 'fred'}
  expected = {
    'text': 'fred',
  }
  result = CodeableConceptFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_codeable_concept_error(mocker):
  he = mock_handle_exception(mocker)
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = CodeableConceptFactory(**params)
  assert result.item is None
  assert mock_called(he)
