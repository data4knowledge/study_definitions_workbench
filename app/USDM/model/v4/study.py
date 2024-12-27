from usdm_model.study import Study as Study
from app.USDM.model.v4.study_version import StudyVersion
from d4kms_generic.logger import application_logger

def first_version(self: Study) -> StudyVersion:
  try:
    return self.versions[0]
  except Exception as e:
    application_logger.exception(f"Exception '{e}' raised finding StudyVersion")
    return None

setattr(Study, 'first_version', first_version)
