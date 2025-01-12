from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.extension import Extension


class ExtensionFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            kwargs["extension"] = []
            self.item = Extension(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
