from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.bundle import BundleEntry


class BundleEntryFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = BundleEntry(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
