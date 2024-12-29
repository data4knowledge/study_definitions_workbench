from usdm_model.address import Address as USDMAddress
from fhir.resources.fhirtypes import AddressType

class AddressFactory():

  def __init__(self, address: USDMAddress):
    try:  
      address_dict = dict(address)
      address_dict.pop('instanceType')
      result = {}
      for k, v in address_dict.items():
        if v:
          result[k] = v
      if 'line' in result:
        result['line'] = [result['line']]
      if 'country' in result:
        result['country'] = address.country.decode
      self.item = AddressType(result)
    except Exception as e:
      self.item = None