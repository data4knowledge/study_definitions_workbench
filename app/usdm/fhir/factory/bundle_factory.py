from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.bundle import Bundle


class BundleFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = Bundle(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
