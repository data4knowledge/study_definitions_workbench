from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.researchstudy import ResearchStudyAssociatedParty
from .coding_factory import CodingFactory
from .codeable_concept_factory import CodeableConceptFactory


class AssociatedPartyFactory(BaseFactory):
    def __init__(self, **kwargs):
        try:
            code = CodingFactory(
                system="http://hl7.org/fhir/research-study-party-role",
                code=kwargs["role_code"],
                display=kwargs["role_display"],
            )
            role = CodeableConceptFactory(coding=[code.item])
            self.item = ResearchStudyAssociatedParty(
                role=role.item, party=kwargs["party"]
            )
        except Exception as e:
            self.item = None
            self.handle_exception(e)
