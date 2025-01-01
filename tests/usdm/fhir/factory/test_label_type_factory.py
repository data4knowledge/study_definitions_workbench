from app.usdm.fhir.factory.label_type_factory import LabelTypeFactory
from usdm_model.code import Code
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

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
  result = LabelTypeFactory(**params)
  assert result.item is not None
  assert (result.item['type'].json()) == '{"coding":[{"system":"codesys","version":"3","code":"code","display":"USA"}]}'
  assert (result.item['value']) == 'xxxxxxxxx'

def test_label_type_error(mocker):
  he = mock_handle_exception(mocker)
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = LabelTypeFactory(**params)
  assert result.item is None
  assert mock_called(he)
