from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.plandefinition import PlanDefinitionAction


class PlanDefinitionActionFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = PlanDefinitionAction(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
