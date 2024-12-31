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
  result = LabelTypeFactory(**params)
  assert result.item is not None
  assert (result.item['type'].json()) == '{"coding":[{"system":"codesys","version":"3","code":"code","display":"USA"}]}'
  assert (result.item['value']) == 'xxxxxxxxx'

def test_label_type_error(mocker, monkeypatch):
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = LabelTypeFactory(**params)
  assert result.item is None

