from app.usdm.fhir.factory.coding_factory import CodingFactory
from usdm_model.code import Code
from tests.usdm.fhir.factory.dict_result import DictResult

def test_coding_usdm():
  usdm_code_dict = {
    'code': 'code',
    'codeSystem': 'codesys',
    'codeSystemVersion': '3',
    'decode': 'USA',
    'id': 'Code1',
    'instanceType': 'Code'
  }
  expected = {
    'code': 'code', 
    'display': 'USA', 
    'system': 'codesys', 
    'version': '3', 
  }
  code = Code(**usdm_code_dict)
  result = CodingFactory(usdm_code=code)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_coding_params():
  params = {'system': 'Code System', 'version': '1', 'code': 'Code', 'display': 'Decode'}
  expected = {
    'code': 'Code', 
    'display': 'Decode', 
    'system': 'Code System', 
    'version': '1', 
  }
  result = CodingFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_coding_error():
  params = {'code': (1,2)} # Force an exception, code not a string type
  result = CodingFactory(**params)
  assert result.item is None
