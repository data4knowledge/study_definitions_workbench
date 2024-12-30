from app.usdm.fhir.factory.coding_factory import CodingFactory
from usdm_model.code import Code

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
    'resource_type': 'Coding', 
    'fhir_comments': None, 
    'extension': None, 
    'id': None, 
    'code': 'code', 
    'display': 'USA', 
    'system': 'codesys', 
    'userSelected': None, 
    'version': '3', 
    'code__ext': None,
    'display__ext': None,
    'system__ext': None,
    'userSelected__ext': None,
    'version__ext': None
  }
  code = Code(**usdm_code_dict)
  result = CodingFactory(usdm_code=code)
  assert result.item is not None
  assert result.item.__dict__ == expected

def test_coding_params():
  params = {'system': 'Code System', 'version': '1', 'code': 'Code', 'display': 'Decode'}
  expected = {
    'resource_type': 'Coding', 
    'fhir_comments': None, 
    'extension': None, 
    'id': None, 
    'code': 'Code', 
    'display': 'Decode', 
    'system': 'Code System', 
    'userSelected': None, 
    'version': '1', 
    'code__ext': None,
    'display__ext': None,
    'system__ext': None,
    'userSelected__ext': None,
    'version__ext': None
  }
  result = CodingFactory(**params)
  assert result.item is not None
  assert result.item.__dict__ == expected

def test_coding_error():
  params = {'code': (1,2)} # Force an exception, code not a string type
  result = CodingFactory(**params)
  assert result.item is None
