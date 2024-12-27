from usdm_model.identifier import StudyIdentifier
from usdm_model.organization import Organization

def is_sponsor(self: StudyIdentifier, organization_map: dict) -> bool:
  org = organization_map[self.scopeId]
  return True if org.type.code == 'C70793' else False

def scoped_by(self: StudyIdentifier, organization_map: dict) -> Organization:
  return organization_map[self.scopeId]

setattr(StudyIdentifier, 'is_sponsor', is_sponsor)
setattr(StudyIdentifier, 'scoped_by', scoped_by)
