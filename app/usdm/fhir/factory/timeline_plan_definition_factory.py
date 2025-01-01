from app.usdm.fhir.factory.base_factory import BaseFactory
from app.usdm.fhir.factory.plan_definition_factory import PlanDefinitionFactory
from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from app.usdm.fhir.factory.coding_factory import CodingFactory
from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from app.usdm.fhir.factory.plan_definition_action_factory import PlanDefinitionActionFactory
from usdm_model.schedule_timeline import ScheduleTimeline
from app.usdm.model.v4.api_base_model import *
from app.usdm.model.v4.schedule_timeline import *

class TimelinePlanDefinitionFactory(BaseFactory):
  
  def __init__(self, timeline: ScheduleTimeline):
    try: 
      self.item = PlanDefinitionFactory(identifier=[self._identifier(timeline).item], status='draft', action=self._actions(timeline)).item
    except Exception as e:
      self.item = None
      self.handle_exception(e)

  def _identifier(self, timeline: ScheduleTimeline):
    plac = CodingFactory(code='PLAC', system='http://terminology.hl7.org/CodeSystem/v2-0203')
    type = CodeableConceptFactory(coding=[plac.item])
    identifier = IdentifierFactory(value=timeline.name, use='usual', type=type.item)
    return identifier

  def _actions(self, timeline: ScheduleTimeline):
    results = []
    timepoints = timeline.timepoint_list()
    for timepoint in timepoints:
      action = PlanDefinitionActionFactory(id=timepoint.id, title=timepoint.label_name(), definitionUri=f'PlanDefinition/{self.fix_id(timepoint.name)}')
      results.append(action.item)
    return results