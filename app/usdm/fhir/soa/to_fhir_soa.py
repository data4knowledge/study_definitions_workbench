import datetime
from d4k_ms_base.logger import application_logger
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
from app.usdm.fhir.factory.activity_definition_factory import ActivityDefinitionFactory
from usdm4.api.study import *
from usdm4.api.study_design import *
from app.usdm.fhir.factory.urn_uuid import URNUUID
from app.usdm.fhir.factory.study_url import StudyUrl


class ToFHIRSoA:
    def __init__(self, study: Study, timeline_id: str, uuid: str, extra: dict = {}):
        """
        Initialize the ToFHIRSoA class
        """
        self._study: Study = study
        self._extra: dict = extra
        self._study_version: StudyVersion = study.first_version()
        self._study_design: StudyDesign = self._study_version.studyDesigns[0]
        self._timeline: ScheduleTimeline = self._study_design.find_timeline(timeline_id)
        self._uuid = uuid

    def to_message(self):
        """
        Build the FHIR SoA message
        """
        try:
            base_url = StudyUrl.generate(self._study)
            entries = []
            date = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            identifier = IdentifierFactory(
                system="urn:ietf:rfc:3986", value=f"urn:uuid:{self._uuid}"
            )

            # Add research study
            rs = ResearchStudyFactory(self._study, self._extra)
            entries.append(
                BundleEntryFactory(
                    request={
                        "method": "PUT",
                        "url": "ResearchStudy",
                    },
                    resource=rs.item,
                    fullUrl=URNUUID.generate(),
                ).item
            )

            # Add timeline plan definition, this is the overall timeline.
            tlpd = TimelinePlanDefinitionFactory(self._study, self._timeline)
            entries.append(
                BundleEntryFactory(
                    request={
                        "method": "PUT",
                        "url": "PlanDefinition",
                    },
                    resource=tlpd.item,
                    fullUrl=URNUUID.generate(),
                ).item
            )
            rs.item.protocol.append({"reference": f"PlanDefinition/{tlpd.item.id}"})

            # Add timepoint plan definitions for the activities
            for index, tp in enumerate(self._timeline.instances):
                tppd = TimepointPlanDefinitionFactory(
                    self._study, self._study_design, tp
                )
                entries.append(
                    BundleEntryFactory(
                        request={
                            "method": "PUT",
                            "url": "PlanDefinition",
                        },
                        resource=tppd.item,
                        fullUrl=URNUUID.generate(),
                    ).item
                )

            # Add activity definitions for each activit
            activity_list = self._study_design.activity_list()
            for index, activity in enumerate(activity_list):
                ad = ActivityDefinitionFactory(
                    id=f"{ActivityDefinitionFactory.fix_id(activity.id)}",
                    name=activity.name,
                    title=activity.label_name(),
                    url=f"{base_url}/ActivityDefinition/{ActivityDefinitionFactory.fix_id(activity.name)}",
                    status="active",
                    description=activity.description,
                )
                entries.append(
                    BundleEntryFactory(
                        request={
                            "method": "PUT",
                            "url": "ActivityDefinition",
                        },
                        resource=ad.item,
                        fullUrl=URNUUID.generate(),
                    ).item
                )

            # Build the final bundle
            bundle = BundleFactory(
                id=f"{BundleFactory.fix_id(self._study.name)}",
                entry=entries,
                type="transaction",
                identifier=identifier.item,
                timestamp=date,
            )
            return bundle.item.json()
        except Exception as e:
            application_logger.exception(
                "Error building FHIR SoA message. See logs for further information", e
            )
            return ""
