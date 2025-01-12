from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.activitydefinition import ActivityDefinition


class ActivityDefinitionFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = ActivityDefinition(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
