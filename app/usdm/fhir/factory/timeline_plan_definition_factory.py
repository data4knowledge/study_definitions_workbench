from app.usdm.fhir.factory.base_factory import BaseFactory
from app.usdm.fhir.factory.plan_definition_factory import PlanDefinitionFactory
from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from app.usdm.fhir.factory.coding_factory import CodingFactory
from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from app.usdm.fhir.factory.plan_definition_action_factory import (
    PlanDefinitionActionFactory,
)
from app.usdm.fhir.factory.plan_definition_related_action_factory import (
    PlanDefinitionRelatedActionFactory,
)
from app.usdm.fhir.factory.extension_factory import ExtensionFactory
from app.usdm.fhir.factory.iso8601_ucum import ISO8601ToUCUM
from usdm4.api.schedule_timeline import ScheduleTimeline
from usdm4.api.timing import Timing
from usdm4.api.study import Study
from usdm4.api.schedule_timeline import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
    ScheduleTimeline,
)
from app.usdm.fhir.factory.cdisc_fhir import CDISCFHIR
from app.usdm.fhir.factory.study_url import StudyUrl


class TimelinePlanDefinitionFactory(BaseFactory):
    def __init__(self, study: Study, timeline: ScheduleTimeline):
        try:
            base_url = StudyUrl.generate(study)
            self.item = PlanDefinitionFactory(
                id=self.fix_id(timeline.id),
                title=timeline.label_name(),
                type=CodeableConceptFactory(
                    coding=[
                        CodingFactory(
                            code="clinical-protocol",
                            system="http://terminology.hl7.org/CodeSystem/plan-definition-type",
                        ).item
                    ]
                ).item,
                purpose=timeline.description,
                identifier=[self._identifier(timeline).item],
                status="active",
                action=self._actions(timeline, base_url),
            ).item
        except Exception as e:
            self.item = None
            self.handle_exception(e)

    def _identifier(self, timeline: ScheduleTimeline):
        plac = CodingFactory(
            code="PLAC", system="http://terminology.hl7.org/CodeSystem/v2-0203"
        )
        type = CodeableConceptFactory(coding=[plac.item])
        identifier = IdentifierFactory(value=timeline.name, use="usual", type=type.item)
        return identifier

    def _actions(self, timeline: ScheduleTimeline, base_url: str) -> list:
        results = []
        timepoints = timeline.timepoint_list()
        for timepoint in timepoints:
            action = PlanDefinitionActionFactory(
                id=self.fix_id(timepoint.id),
                title=timepoint.label_name(),
                # definitionUri=f"PlanDefinition-{self.fix_id(timepoint.name)}",
                definitionCanonical=f"{base_url}/PlanDefinition/{self.fix_id(timepoint.name)}",
                relatedAction=[],
            )
            if ra := self._related_action(timeline, timepoint):
                action.item.relatedAction.append(ra)
            results.append(action.item)
        return results

    def _related_action(
        self,
        timeline: ScheduleTimeline,
        timepoint: ScheduledDecisionInstance | ScheduledActivityInstance,
    ) -> dict | None:
        timing: Timing = timeline.find_timing_from(timepoint.id)
        if timing.type.decode == "Fixed Reference":
            return None
        offset = ISO8601ToUCUM.convert(timing.value)
        related = PlanDefinitionRelatedActionFactory(
            targetId=self.fix_id(timing.relativeToScheduledInstanceId),
            relationship=CDISCFHIR.from_c201264(timing.type),
            offsetDuration=offset,
            extension=[],
        )
        if timing.windowLower:
            window = ExtensionFactory(
                **{
                    "valueRange": {
                        "low": ISO8601ToUCUM.convert(timing.windowLower),
                        "high": ISO8601ToUCUM.convert(timing.windowUpper),
                    },
                    "url": "http://hl7.org/fhir/uv/vulcan-schedule/StructureDefinition/AcceptableOffsetRangeSoa",
                }
            )
            related.item.extension.append(window.item)
        return related.item
