from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.coding import Coding


class CodingFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            if "usdm_code" in kwargs:
                kwargs["system"] = kwargs["usdm_code"].codeSystem
                kwargs["version"] = kwargs["usdm_code"].codeSystemVersion
                kwargs["code"] = kwargs["usdm_code"].code
                kwargs["display"] = kwargs["usdm_code"].decode
                kwargs.pop("usdm_code")
            self.item = Coding(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
