from app.usdm.fhir.factory.base_factory import BaseFactory
from app.usdm.fhir.factory.plan_definition_factory import PlanDefinitionFactory
from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from app.usdm.fhir.factory.coding_factory import CodingFactory
from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from app.usdm.fhir.factory.plan_definition_action_factory import PlanDefinitionActionFactory
from app.usdm.fhir.factory.plan_definition_related_action_factory import PlanDefinitionRelatedActionFactory
from app.usdm.fhir.factory.iso8601_ucum import ISO8601ToUCUM
from usdm_model.schedule_timeline import ScheduleTimeline
from usdm_model.scheduled_instance import ScheduledActivityInstance, ScheduledDecisionInstance
from usdm_model.timing import Timing
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

  def _actions(self, timeline: ScheduleTimeline) -> list:
    results = []
    timepoints = timeline.timepoint_list()
    for timepoint in timepoints:
      action = PlanDefinitionActionFactory(id=timepoint.id, title=timepoint.label_name(), definitionUri=f'PlanDefinition/{self.fix_id(timepoint.name)}', relatedAction=[self._related_action(timeline, timepoint)])
      results.append(action.item)
    return results
  
  def _related_action(self, timeline: ScheduleTimeline, timepoint: ScheduledDecisionInstance | ScheduledActivityInstance) -> dict:
    timing: Timing = timeline.find_timing_from(timepoint.id)
    offset = ISO8601ToUCUM.convert(timing.value)
    related = PlanDefinitionRelatedActionFactory(targetId=self.fix_id(timing.id), relationship=timing.type.decode, offsetDuration=offset)
    return related.item
  



  # class ConditionAssignment(ApiBaseModelWithId):
  # condition: str
  # conditionTargetId: str
  # instanceType: Literal['ConditionAssignment']
# 
# class ScheduledInstance(ApiBaseModelWithIdNameLabelAndDesc):
  # defaultConditionId: Union[str, None] = None
  # epochId: Union[str, None] = None
  # instanceType: Literal['ScheduledInstance']
# 
# class ScheduledActivityInstance(ScheduledInstance):
  # timelineId: Union[str, None] = None
  # timelineExitId: Union[str, None] = None
  # activityIds: List[str] = []
  # encounterId: Union[str, None] = None
  # instanceType: Literal['ScheduledActivityInstance']
# 
# class ScheduledDecisionInstance(ScheduledInstance):
# conditionAssignments: List[ConditionAssignment] = [] # Allow for empty list, not in API
# instanceType: Literal['ScheduledDecisionInstance']
# 
# 

# class Timing(ApiBaseModelWithIdNameLabelAndDesc):
#   type: Code
#   value: str
#   valueLabel: str
#   relativeToFrom: Code
#   relativeFromScheduledInstanceId: str
#   relativeToScheduledInstanceId: Union[str, None] = None
#   windowLower: Union[str, None] = None
#   windowUpper: Union[str, None] = None
#   windowLabel: Union[str, None] = None
#   instanceType: Literal['Timing']  