from app.usdm.fhir.factory.base_factory import BaseFactory
from usdm_model.address import Address as USDMAddress
from fhir.resources.fhirtypes import AddressType


class AddressFactory(BaseFactory):
    def __init__(self, address: USDMAddress):
        try:
            address_dict = dict(address)
            address_dict.pop("instanceType")
            result = {}
            for k, v in address_dict.items():
                if v:
                    result[k] = v
            if "lines" in result:
                result["line"] = result["lines"]
                result.pop("lines")
            if "country" in result:
                result["country"] = address.country.decode
            self.item = AddressType(**result)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
