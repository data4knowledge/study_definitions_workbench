import traceback

from app.usdm.fhir.factory.base_factory import BaseFactory
from app.usdm.fhir.factory.plan_definition_factory import PlanDefinitionFactory
from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from app.usdm.fhir.factory.coding_factory import CodingFactory
from usdm_model.schedule_timeline import ScheduleTimeline

class TimelinePlanDefinitionFactory(BaseFactory):
  
  def __init__(self, timeline: ScheduleTimeline):
    try: 
      self.item = PlanDefinitionFactory(identifier=[self._identifier(timeline)]).item
    except Exception as e:
      print(f"EXCEPTION: {e}\n{traceback.format_exc()}")
      self.item = None

  def _identifier(self, timeline: ScheduleTimeline):
    type = CodingFactory(code='PLAC', system='http://terminology.hl7.org/CodeSystem/v2-0203')
    return IdentifierFactory(value=timeline.name, use='usual', coding=[type])