from usdm_model.study_version import StudyVersion
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
    if x.is_sponsor():
      return x.studyIdentifier
  return None

def sponsor_name(self: StudyVersion) -> str:
  for x in self.studyIdentifiers:
    if x.is_sponsor():
      return x.studyIdentifierScope.name
  return ''

def nct_identifier(self: StudyVersion) -> StudyIdentifier:
  for identifier in self.studyIdentifiers:
    if identifier.studyIdentifierScope.name == 'ClinicalTrials.gov':
      return identifier.studyIdentifier
  return None

def protocol_date(self: StudyVersion) -> StudyIdentifier:
  for x in self.dateValues:
    if x.type.decode == 'Protocol Effective Date':
      return x.dateValue
  return ''

def approval_date(self: StudyVersion) -> StudyIdentifier:
  for x in self.dateValues:
    print(f"A: {x}")
    if x.type.decode == 'Sponsor Approval Date':
      print(f"B: {x}")
      return x.dateValue
  return ''

setattr(StudyVersion, 'official_title', official_title)
setattr(StudyVersion, 'short_title', short_title)
setattr(StudyVersion, 'acronym', acronym)
setattr(StudyVersion, 'sponsor_identifier', sponsor_identifier)
setattr(StudyVersion, 'sponsor_name', sponsor_name)
setattr(StudyVersion, 'nct_identifier', nct_identifier)
setattr(StudyVersion, 'protocol_date', protocol_date)
setattr(StudyVersion, 'approval_date', approval_date)
