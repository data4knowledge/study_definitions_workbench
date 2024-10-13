from usdm_model.study_identifier import StudyIdentifier

def is_sponsor(self: StudyIdentifier) -> bool:
  return True if self.studyIdentifierScope.organizationType.code == 'C70793' else False

def is_nct_identifier(self: StudyIdentifier) -> bool:
  return True if self.studyIdentifierScope.name == 'ClinicalTrials.gov' else False

setattr(StudyIdentifier, 'is_sponsor', is_sponsor)
setattr(StudyIdentifier, 'is_nct_identifier', is_nct_identifier)
