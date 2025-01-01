import datetime

from usdm_model.study import Study
from usdm_model.study_version import StudyVersion
from usdm_model.study_design import StudyDesign
from usdm_model.schedule_timeline import ScheduleTimeline
from usdm_db.cross_reference import CrossReference
from usdm_db.errors_and_logging.errors_and_logging import ErrorsAndLogging

from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from app.usdm.fhir.factory.research_study_factory import ResearchStudyFactory
from app.usdm.fhir.factory.bundle_factory import BundleFactory
from app.usdm.fhir.factory.bundle_entry_factory import BundleEntryFactory
from app.usdm.fhir.factory.timeline_plan_definition_factory import TimelinePlanDefinitionFactory
from app.usdm.fhir.factory.timepoint_plan_definition_factory import TimepointPlanDefinitionFactory


class ToFHIRSoA():
  
  def __init__(self, study: Study, extra: dict={}):
    self._study: Study = study
    self._extra: dict = extra
    self._errors_and_logging = ErrorsAndLogging()
    self._cross_ref = CrossReference(study, self._errors_and_logging)
    self._study_version: StudyVersion = study.first_versions
    self._study_design: StudyDesign = self._study_version[0]
    self._timeline: ScheduleTimeline = self._study_design.main_timeline()

  def to_message(self):
    try:
      entries = []
      date = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
      identifier = IdentifierFactory(system='urn:ietf:rfc:3986', value=f'urn:uuid:{self._study.id}')
      rs = ResearchStudyFactory(self._study, self._extra)
      tlpd = TimelinePlanDefinitionFactory(self._timeline)
      entries.append(BundleEntryFactory(resource=rs, fullUrl='https://www.example.com/Composition/1234A'))
      entries.append(BundleEntryFactory(resource=tlpd, fullUrl='https://www.example.com/Composition/1234B'))
      for tp in self._timeline.instances:
        tppd = TimepointPlanDefinitionFactory(self._study_design, tp)
        entries.append(BundleEntryFactory(resource=tppd, fullUrl='https://www.example.com/Composition/1234B'))
      bundle = BundleFactory(entry=entries, type="document", identifier=identifier, timestamp=date)
      return bundle.json()
    except Exception as e:
      self._errors_and_logging
      return ''