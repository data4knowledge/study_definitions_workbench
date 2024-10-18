from usdm_model.identifier import StudyIdentifier

def is_sponsor(self: StudyIdentifier, organization_map: dict) -> bool:
  print(f"ORG: {organization_map}")
  org = organization_map[self.scopeId]
  return True if org.type.code == 'C70793' else False

# def is_nct_identifier(self: StudyIdentifier) -> bool:
#   return True if self.studyIdentifierScope.name == 'ClinicalTrials.gov' else False

setattr(StudyIdentifier, 'is_sponsor', is_sponsor)
# setattr(StudyIdentifier, 'is_nct_identifier', is_nct_identifier)
