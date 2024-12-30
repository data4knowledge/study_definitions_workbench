from usdm_model.study import Study
from usdm_db.cross_reference import CrossReference
from usdm_db.errors_and_logging.errors_and_logging import ErrorsAndLogging

from usdm.fhir.factory.research_study_factory import ResearchStudyFactory

class ToFHIRSoA():
  
  def __init__(self, study: Study, timeline_name: str, extra: dict={}):
    self._study = study
    self._extra = extra
    self._errors_and_logging = ErrorsAndLogging()
    self._cross_ref = CrossReference(study, self._errors_and_logging)
    self._study_version = study.versions[0]
    self._study_design = self.study_version.studyDesigns[0]

  def to_soa(self):
    try:
      rs = ResearchStudyFactory(self._study, self._extra)
    except Exception as e:
      pass