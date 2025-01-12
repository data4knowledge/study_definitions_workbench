from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.codeableconcept import CodeableConcept


class CodeableConceptFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            self.item = CodeableConcept(**kwargs)
        except Exception as e:
            self.item = None
            self.handle_exception(e)
