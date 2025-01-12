from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.fhirtypes import ResearchStudyLabelType
from .coding_factory import CodingFactory
from .codeable_concept_factory import CodeableConceptFactory


class LabelTypeFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            coding = CodingFactory(usdm_code=kwargs["usdm_code"])
            type = CodeableConceptFactory(coding=[coding.item])
            self.item = ResearchStudyLabelType(type=type.item, value=kwargs["text"])
        except Exception as e:
            self.item = None
            self.handle_exception(e)
