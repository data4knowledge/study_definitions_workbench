from app.usdm.fhir.factory.progress_status_factory import ProgressStatusFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

def test_progress_status():
  params = {'state_code': 'xxx', 'state_display': 'yyy', 'value': '1234'}
  expected = {
    'period': {
      'start': '1234',
    },
    'state': {
      'coding': [
          {
            'code': 'xxx',
            'display': 'yyy',
            'system': 'http://hl7.org/fhir/research-study-party-role',
          },
      ],
    },
  }
  result = ProgressStatusFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_codeable_concept_error(mocker):
  he = mock_handle_exception(mocker)
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = ProgressStatusFactory(**params)
  assert result.item is None
  assert mock_called(he)
