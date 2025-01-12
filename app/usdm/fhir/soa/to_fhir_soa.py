import datetime
from d4kms_generic.logger import application_logger
from usdm_model.study import Study
from usdm_model.study_version import StudyVersion
from usdm_model.study_design import StudyDesign
from usdm_model.schedule_timeline import ScheduleTimeline

from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from app.usdm.fhir.factory.research_study_factory import ResearchStudyFactory
from app.usdm.fhir.factory.bundle_factory import BundleFactory
from app.usdm.fhir.factory.bundle_entry_factory import BundleEntryFactory
from app.usdm.fhir.factory.timeline_plan_definition_factory import (
    TimelinePlanDefinitionFactory,
)
from app.usdm.fhir.factory.timepoint_plan_definition_factory import (
    TimepointPlanDefinitionFactory,
)

from app.usdm.model.v4.study import *
from app.usdm.model.v4.study_design import *


class ToFHIRSoA:
    def __init__(self, study: Study, timeline_id: str, uuid: str, extra: dict = {}):
        self._study: Study = study
        self._extra: dict = extra
        self._study_version: StudyVersion = study.first_version()
        self._study_design: StudyDesign = self._study_version.studyDesigns[0]
        self._timeline: ScheduleTimeline = self._study_design.find_timeline(timeline_id)
        self._uuid = uuid

    def to_message(self):
        try:
            entries = []
            date = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            identifier = IdentifierFactory(
                system="urn:ietf:rfc:3986", value=f"urn:uuid:{self._uuid}"
            )
            rs = ResearchStudyFactory(self._study, self._extra)
            tlpd = TimelinePlanDefinitionFactory(self._timeline)
            entries.append(
                BundleEntryFactory(
                    resource=rs.item,
                    fullUrl="https://www.example.com/Composition/1234A",
                ).item
            )
            entries.append(
                BundleEntryFactory(
                    resource=tlpd.item,
                    fullUrl="https://www.example.com/Composition/1234B",
                ).item
            )
            for tp in self._timeline.instances:
                tppd = TimepointPlanDefinitionFactory(self._study_design, tp)
                entries.append(
                    BundleEntryFactory(
                        resource=tppd.item,
                        fullUrl="https://www.example.com/Composition/1234B",
                    ).item
                )
            bundle = BundleFactory(
                entry=entries,
                type="document",
                identifier=identifier.item,
                timestamp=date,
            )
            return bundle.item.json()
        except Exception as e:
            application_logger.exception(
                "Error building FHIR SoA message. See logs for further information", e
            )
            return ""
