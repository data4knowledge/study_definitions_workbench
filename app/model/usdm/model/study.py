from usdm_model.study import Study as Study
from app.model.usdm.model.study_version import StudyVersion

def first_version(self: Study) -> StudyVersion:
  return self.versions[0]

setattr(Study, 'first_version', first_version)
