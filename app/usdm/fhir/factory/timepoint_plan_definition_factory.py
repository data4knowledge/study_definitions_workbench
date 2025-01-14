from app.usdm.fhir.factory.base_factory import BaseFactory
from app.usdm.fhir.factory.plan_definition_factory import PlanDefinitionFactory
from app.usdm.fhir.factory.coding_factory import CodingFactory
from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from app.usdm.fhir.factory.plan_definition_action_factory import (
    PlanDefinitionActionFactory,
)
from usdm_model.study_design import StudyDesign
from usdm_model.scheduled_instance import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
)
from app.usdm.model.v4.api_base_model import *
from app.usdm.model.v4.study_design import *


class TimepointPlanDefinitionFactory(BaseFactory):
    def __init__(
        self,
        study_design: StudyDesign,
        timepoint: ScheduledDecisionInstance | ScheduledActivityInstance,
    ):
        try:
            self.item = PlanDefinitionFactory(
                id=self.fix_id(timepoint.id),
                title=timepoint.label_name(),
                type=CodeableConceptFactory(
                    coding=[
                        CodingFactory(
                            code="clinical-protocol",
                            system="http://terminology.hl7.org/CodeSystem/plan-definition-type",
                        ).item
                    ]
                ).item,
                #       date=
                #       version=
                purpose=timepoint.description,
                status="draft",
                action=self._actions(study_design, timepoint),
            ).item
        except Exception as e:
            self.item = None
            self.handle_exception(e)

    def _actions(
        self,
        study_design: StudyDesign,
        timepoint: ScheduledDecisionInstance | ScheduledActivityInstance,
    ) -> list:
        results = []
        activity_list = study_design.activity_list()
        activities = {v.id: v for v in activity_list}
        for id in timepoint.activityIds:
            activity = activities[id]
            action = PlanDefinitionActionFactory(
                id=self.fix_id(activity.id),
                title=activity.label_name(),
                definitionUri=f"ActivityDefinition-{self.fix_id(activity.name)}",
            )
            results.append(action.item)
        return results
