from usdm_model.study_design import StudyDesign
from usdm_model.study_version import StudyVersion
from usdm_model.organization import Organization
from usdm_model.governance_date import GovernanceDate
from usdm_model.eligibility_criterion import EligibilityCriterion
from app.usdm.model.v4.study_title import *
from app.usdm.model.v4.study_identifier import *
from app.usdm.model.v4.study_design import *
from datetime import date

def official_title_text(self: StudyVersion) -> str:
  for x in self.titles:
    if x.is_official():
      return x.text
  return ''

def short_title_text(self: StudyVersion) -> str:
  for x in self.titles:
    if x.is_short():
      return x.text
  return ''

def acronym_text(self: StudyVersion) -> str:
  for x in self.titles:
    if x.is_acronym():
      return x.text
  return ''

def official_title(self: StudyVersion) -> StudyIdentifier:
  for x in self.titles:
    if x.is_official():
      return x
  return None

def short_title(self: StudyVersion) -> StudyIdentifier:
  for x in self.titles:
    if x.is_short():
      return x
  return None

def acronym(self: StudyVersion) -> StudyIdentifier:
  for x in self.titles:
    if x.is_acronym():
      return x
  return None

def sponsor(self: StudyVersion) -> Organization:
  map = self.organization_map()
  for x in self.studyIdentifiers:
    if x.is_sponsor(map):
      return map[x.scopeId]
  return None

# Note: Method sponsor_identifier in base USDM class

def sponsor_identifier_text(self: StudyVersion) -> StudyIdentifier:
  for x in self.studyIdentifiers:
    if x.is_sponsor(self.organization_map()):
      return x.text
  return ''

def sponsor_name(self: StudyVersion) -> str:
  map = self.organization_map()
  for x in self.studyIdentifiers:
    if x.is_sponsor(map):
      return map[x.scopeId].name 
  return ''

def sponsor_address(self: StudyVersion) -> str:
  map = self.organization_map()
  for x in self.studyIdentifiers:
    if x.is_sponsor(map):
      return map[x.scopeId].legalAddress.text
  return ''

def nct_identifier(self: StudyVersion) -> StudyIdentifier:
  map = self.organization_map()
  for x in self.studyIdentifiers:
    if map[x.scopeId].name == 'ClinicalTrials.gov':
      return x.text
  return ''

def protocol_date(self: StudyVersion) -> GovernanceDate:
  for x in self.dateValues:
    if x.type.decode == 'Protocol Effective Date':
      return x
  return ''

def approval_date(self: StudyVersion) -> GovernanceDate:
  for x in self.dateValues:
    if x.type.decode == 'Sponsor Approval Date':
      return x
  return ''

def protocol_date_value(self: StudyVersion) -> date:
  for x in self.dateValues:
    if x.type.decode == 'Protocol Effective Date':
      return x.dateValue
  return ''

def approval_date_value(self: StudyVersion) -> date:
  for x in self.dateValues:
    if x.type.decode == 'Sponsor Approval Date':
      return x.dateValue
  return ''

def organization_map(self: StudyVersion) -> Organization:
  return {x.id: x for x in self.organizations}

def criterion_map(self: StudyVersion) -> EligibilityCriterion:
  return {x.id: x for x in self.criteria}

def find_study_design(self: StudyVersion, id: str) -> StudyDesign:
  return next((x for x in self.studyDesigns if x.id == id), None)

setattr(StudyVersion, 'official_title_text', official_title_text)
setattr(StudyVersion, 'short_title_text', short_title_text)
setattr(StudyVersion, 'acronym_text', acronym_text)
setattr(StudyVersion, 'official_title', official_title)
setattr(StudyVersion, 'short_title', short_title)
setattr(StudyVersion, 'acronym', acronym)
setattr(StudyVersion, 'sponsor', sponsor)
setattr(StudyVersion, 'sponsor_identifier_text', sponsor_identifier_text)
setattr(StudyVersion, 'sponsor_name', sponsor_name)
setattr(StudyVersion, 'sponsor_address', sponsor_address)
setattr(StudyVersion, 'nct_identifier', nct_identifier)
setattr(StudyVersion, 'protocol_date', protocol_date)
setattr(StudyVersion, 'approval_date', approval_date)
setattr(StudyVersion, 'protocol_date_value', protocol_date_value)
setattr(StudyVersion, 'approval_date_value', approval_date_value)
setattr(StudyVersion, 'organization_map', organization_map)
setattr(StudyVersion, 'criterion_map', criterion_map)
setattr(StudyVersion, 'find_study_design', find_study_design)
