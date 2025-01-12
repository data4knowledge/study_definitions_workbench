from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.researchstudy import ResearchStudyProgressStatus
from .coding_factory import CodingFactory
from .codeable_concept_factory import CodeableConceptFactory


class ProgressStatusFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            code = CodingFactory(
                system="http://hl7.org/fhir/research-study-party-role",
                code=kwargs["state_code"],
                display=kwargs["state_display"],
            )
            state = CodeableConceptFactory(coding=[code.item])
            self.item = ResearchStudyProgressStatus(
                state=state.item, period={"start": kwargs["value"]}
            )
        except Exception as e:
            self.item = None
            self.handle_exception(e)
