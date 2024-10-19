from usdm_model.study_version import StudyVersion
from usdm_model.organization import Organization
from app.model.usdm.model.study_title import *
from app.model.usdm.model.study_identifier import *

def official_title(self: StudyVersion) -> str:
  for x in self.titles:
    if x.is_official():
      return x.text
  return ''

def short_title(self: StudyVersion) -> str:
  for x in self.titles:
    if x.is_short():
      return x.text
  return ''

def acronym(self: StudyVersion) -> str:
  for x in self.titles:
    if x.is_acronym():
      return x.text
  return ''

def sponsor_identifier(self: StudyVersion) -> StudyIdentifier:
  for x in self.studyIdentifiers:
    #print(f"SPONSOR: {x}")
    if x.is_sponsor(self.organization_map()):
      return x.text
  return ''

def sponsor_name(self: StudyVersion) -> str:
  map = self.organization_map()
  for x in self.studyIdentifiers:
    if x.is_sponsor(map):
      return map[x.scopeId].name 
  return ''

def nct_identifier(self: StudyVersion) -> StudyIdentifier:
  map = self.organization_map()
  for x in self.studyIdentifiers:
    if map[x.scopeId].name == 'ClinicalTrials.gov':
      return x.text
  return ''

def protocol_date(self: StudyVersion) -> StudyIdentifier:
  for x in self.dateValues:
    if x.type.decode == 'Protocol Effective Date':
      return x.dateValue
  return ''

def approval_date(self: StudyVersion) -> StudyIdentifier:
  for x in self.dateValues:
    #print(f"A: {x}")
    if x.type.decode == 'Sponsor Approval Date':
      #print(f"B: {x}")
      return x.dateValue
  return ''

def organization_map(self: StudyVersion) -> Organization:
  return {x.id: x for x in self.organizations}

setattr(StudyVersion, 'official_title', official_title)
setattr(StudyVersion, 'short_title', short_title)
setattr(StudyVersion, 'acronym', acronym)
setattr(StudyVersion, 'sponsor_identifier', sponsor_identifier)
setattr(StudyVersion, 'sponsor_name', sponsor_name)
setattr(StudyVersion, 'nct_identifier', nct_identifier)
setattr(StudyVersion, 'protocol_date', protocol_date)
setattr(StudyVersion, 'approval_date', approval_date)
setattr(StudyVersion, 'organization_map', organization_map)
