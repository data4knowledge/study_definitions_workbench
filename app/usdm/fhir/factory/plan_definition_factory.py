from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.plandefinition import PlanDefinition


class PlanDefinitionFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = PlanDefinition(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
