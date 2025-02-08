from usdm_model.study import Study
from app.usdm.fhir.factory.base_factory import BaseFactory


class StudyUrl:
    @classmethod
    def generate(cls, study: Study) -> str:
        return f"http://d4k.dk/fhir/vulcan-soa/{BaseFactory.fix_id(study.name)}"
