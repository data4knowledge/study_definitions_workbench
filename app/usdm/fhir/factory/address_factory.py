from usdm_model.address import Address as USDMAddress
from fhir.resources.fhirtypes import AddressType

class AddressFactory():

  def __init__(self, address: USDMAddress):  
    x = dict(address)
    x.pop('instanceType')
    y = {}
    for k, v in x.items():
      if v:
        y[k] = v
    if 'line' in y:
      y['line'] = [y['line']]
    if 'country' in y:
      y['country'] = address.country.decode
    self.item = AddressType(y)
