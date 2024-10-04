from d4kms_generic.service import Service
from d4kms_generic.service_environment import ServiceEnvironment

class AddressService(Service):

  def __init__(self):
    se = ServiceEnvironment()
    url = se.get('ADDRESS_SERVER_URL')
    super().__init__(url)

  def parser(self, address: str) -> dict:
    return super().post('parser', data={'query': address})
