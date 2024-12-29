from app.usdm.fhir.factory.address_factory import AddressFactory
from usdm_model.address import Address

def test_address(mocker, monkeypatch):
  address_dict = {
    'city': 'city',
    'country': {
      'code': 'code',
      'codeSystem': 'codesys',
      'codeSystemVersion': '3',
      'decode': 'USA',
      'id': 'Code1',
      'instanceType': 'Code'
    },
    'district': 'district',
    'id': 'Addr_1',
    'instanceType': 'Address',
    'lines': ['line 1'],
    'postalCode': 'postal code',
    'state': 'state',
    'text': 'line 1, city, district, state, postal code, USA'
  }
  expected = {
    'city': 'city',
    'country': 'USA',
    'district': 'district',
    'id': 'Addr_1',
    'postalCode': 'postal code',
    'state': 'state',
    'text': 'line 1, city, district, state, postal code, USA',
  }
  address = Address(**address_dict)
  result = AddressFactory(address)
  assert result.item is not None
  assert result.item == expected

def test_address_error(mocker, monkeypatch):
  result = AddressFactory({})
  assert result.item is None
