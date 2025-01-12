from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.plandefinition import PlanDefinitionActionRelatedAction


class PlanDefinitionRelatedActionFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = PlanDefinitionActionRelatedAction(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
