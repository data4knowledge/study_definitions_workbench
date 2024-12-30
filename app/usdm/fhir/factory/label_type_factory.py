from fhir.resources.fhirtypes import ResearchStudyLabelType
from .coding_factory import CodingFactory
from .codeable_concept_factory import CodeableConceptFactory

class LabelTypeFactory():
  
  def __init__(self, **kwargs):
    try: 
      print(f"USDM: {kwargs}")
      coding = CodingFactory(usdm_code=kwargs['usdm_code'])
      print(f"C: {coding.item}")
      type = CodeableConceptFactory(coding=[coding.item]) 
      print(f"T: {type.item}")
      self.item = ResearchStudyLabelType(type=type.item, value=kwargs['text'])
    except Exception as e:
      print(f"Exception: {e}")
      self.item = None
