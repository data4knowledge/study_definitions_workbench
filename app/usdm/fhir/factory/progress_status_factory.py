from fhir.resources.researchstudy import ResearchStudyProgressStatus
from .coding_factory import CodingFactory
from .codeable_concept_factory import CodeableConceptFactory

class ProgressStatusFactory():
  
  def __init__(self, **kwargs):
    try: 
      code = CodingFactory(system='http://hl7.org/fhir/research-study-party-role', code=kwargs['state_code'], display=kwargs['state_display'])
      state = CodeableConceptFactory(coding=[code])
      return ResearchStudyProgressStatus(state=state, period={'start': kwargs['value']})
    except Exception as e:
      return None
