import traceback

from app.usdm.fhir.factory.base_factory import BaseFactory
from app.usdm.fhir.factory.plan_definition_factory import PlanDefinitionFactory
from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from app.usdm.fhir.factory.coding_factory import CodingFactory
from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from usdm_model.schedule_timeline import ScheduleTimeline

class TimelinePlanDefinitionFactory(BaseFactory):
  
  def __init__(self, timeline: ScheduleTimeline):
    try: 
      print(f"TIME: {timeline.name}")
      self.item = PlanDefinitionFactory(identifier=[self._identifier(timeline).item], status='draft').item
    except Exception as e:
      print(f"TPD EXCEPTION: {e}\n{traceback.format_exc()}")
      self.item = None

  @staticmethod
  def _identifier(timeline: ScheduleTimeline):
    plac = CodingFactory(code='PLAC', system='http://terminology.hl7.org/CodeSystem/v2-0203')
    type = CodeableConceptFactory(coding=[plac.item])
    identifier = IdentifierFactory(value=timeline.name, use='usual', type=type.item)
    return identifier
