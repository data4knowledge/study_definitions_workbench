from usdm_model.wrapper import Wrapper
from usdm_model.study import Study
from usdm_model.study_design import StudyDesign
from usdm_model.study_version import StudyVersion
from usdm_model.study_title import StudyTitle
from usdm_model.study_protocol_document import StudyProtocolDocument
from usdm_model.study_protocol_document_version import StudyProtocolDocumentVersion
from usdm_model.population_definition import StudyDesignPopulation
from usdm_model.eligibility_criterion import EligibilityCriterion
from usdm_model.study_identifier import StudyIdentifier
from usdm_model.organization import Organization
from usdm_model.address import Address
from usdm_model.narrative_content import NarrativeContent
from usdm_model.study_amendment import StudyAmendment
from usdm_model.study_amendment_reason import StudyAmendmentReason
from usdm_excel.globals import Globals
from uuid import uuid4
from usdm_info import __model_version__ as usdm_version, __package_version__ as system_version
from d4kms_generic import application_logger
from app.model.m11_protocol.m11_title_page import M11TitlePage
from app.model.m11_protocol.m11_inclusion_exclusion import M11InclusionExclusion
from app.model.m11_protocol.m11_estimands import M11IEstimands
from app.model.m11_protocol.m11_amendment import M11IAmendment
from app.model.m11_protocol.m11_sections import M11Sections
from app.model.m11_protocol.m11_utility import *

class M11ToUSDM():
  
  DIV_OPEN_NS = '<div xmlns="http://www.w3.org/1999/xhtml">'
  DIV_CLOSE = '</div>'

  def __init__(self, title_page: M11TitlePage, inclusion_exclusion: M11InclusionExclusion, estimands: M11IEstimands, amendment: M11IAmendment, sections: M11Sections, globals: Globals, system_name, system_version):
    self._globals = globals
    self._title_page = title_page
    self._inclusion_exclusion = inclusion_exclusion
    self._estimands = estimands
    self._amendment = amendment
    self._sections = sections
    self._id_manager = self._globals.id_manager
    self._cdisc_ct_library = self._globals.cdisc_ct_library
    self._system_name = system_name
    self._system_version = system_version

  def export(self) -> Wrapper:
    try:
      study = self._study()
      doc_version = self._document_version(study)
      root = model_instance(NarrativeContent, {'name': 'ROOT', 'sectionNumber': '0', 'sectionTitle': 'Root', 'text': '', 'childIds': [], 'previousId': None, 'nextId': None}, self._id_manager)
      doc_version.contents.append(root)
      local_index = self._section_to_narrative(root, 0, 1, doc_version)
      self._double_link(doc_version.contents, 'previousId', 'nextId')
      return Wrapper(study=study, usdmVersion=usdm_version, systemName=self._system_name, systemVersion=self._system_version).to_json()
    except Exception as e:
      application_logger.exception(f"Exception raised parsing M11 content. See logs for more details", e)
      return None

  def _section_to_narrative(self, parent, index, level, doc_version) -> int:
    process = True
    previous = None
    local_index = index
    loop = 0
    while process:
      section = self._sections.sections[local_index]
      if section.level == level:
        sn = section.number if section.number else ''
        st = section.title if section.title else ''
        nc_text = f"{self.DIV_OPEN_NS}{section.to_html()}{self.DIV_CLOSE}"
        nc = model_instance(NarrativeContent, {'name': f"NC-{sn}", 'sectionNumber': sn, 'sectionTitle': st, 'text': nc_text, 'childIds': [], 'previousId': None, 'nextId': None}, self._id_manager)
        doc_version.contents.append(nc)
        parent.childIds.append(nc.id)
        previous = nc
        local_index += 1
      elif section.level > level: 
        if previous:
          local_index = self._section_to_narrative(previous, local_index, level + 1, doc_version)
        else:
          application_logger.error(f"No previous set processing sections")
          local_index += 1
      elif section.level < level: 
        return local_index
      if local_index >= len(self._sections.sections):
        process = False
    return local_index
    
  def _study(self):
    sponsor_title_code = cdisc_ct_code('C99905x2', 'Official Study Title', self._cdisc_ct_library, self._id_manager)
    protocl_status_code = cdisc_ct_code('C85255', 'Draft', self._cdisc_ct_library, self._id_manager)
    intervention_model_code = cdisc_ct_code('C82639', 'Parallel Study', self._cdisc_ct_library, self._id_manager)
    sponsor_code = cdisc_ct_code("C70793", 'Clinical Study Sponsor', self._cdisc_ct_library, self._id_manager)
    study_title = model_instance(StudyTitle, {'text': self._title_page.full_title, 'type': sponsor_title_code}, self._id_manager)
    protocl_document_version = model_instance(StudyProtocolDocumentVersion, {'protocolVersion': '1', 'protocolStatus': protocl_status_code}, self._id_manager)
    protocl_document = model_instance(StudyProtocolDocument, {'name': 'PROTOCOL V1', 'label': '', 'description': '', 'versions': [protocl_document_version]}, self._id_manager)
    population = self._population()
    study_design = model_instance(StudyDesign, {'name': 'Study Design', 'label': '', 'description': '', 
      'rationale': 'XXX', 'interventionModel': intervention_model_code, 'arms': [], 'studyCells': [], 
      'epochs': [], 'population': population}, self._id_manager)
    sponsor_address = self._title_page.sponsor_address
    #print(f"ADDRESS: {sponsor_address}")
    address = model_instance(Address, sponsor_address, self._id_manager)
    organization = model_instance(Organization, {'name': self._title_page.sponsor_name, 'organizationType': sponsor_code, 'identifier': "123456789", 'identifierScheme': "DUNS", 'legalAddress': address}, self._id_manager) 
    identifier = model_instance(StudyIdentifier, {'studyIdentifier': self._title_page.sponsor_protocol_identifier, 'studyIdentifierScope': organization}, self._id_manager)
    params = {
      'versionIdentifier': '1', 
      'rationale': 'XXX', 
      'titles': [study_title], 
      'studyDesigns': [study_design], 
      'documentVersionId': protocl_document_version.id, 
      'studyIdentifiers': [identifier], 
      'studyPhase': self._title_page.trial_phase, 
      'amendments': self._get_amendments()
    }
    study_version = model_instance(StudyVersion, params, self._id_manager) 
    study = model_instance(Study, {'id': uuid4(), 'name': self._title_page.study_name, 'label': '', 'description': '', 'versions': [study_version], 'documentedBy': protocl_document}, self._id_manager) 
    return study

  def _population(self):
    results = []
    inc = cdisc_ct_code('C25532', 'INCLUSION', self._cdisc_ct_library, self._id_manager)
    exc = cdisc_ct_code('C25370', 'EXCLUSION', self._cdisc_ct_library, self._id_manager)
    for index, text in enumerate(self._inclusion_exclusion.inclusion):
      params = {'name': f'INC{index+1}', 'label': f'Inclusion {index+1} ', 'description': '', 'text': text, 'category': inc, 'identifier': f'{index + 1}'}
      results.append(model_instance(EligibilityCriterion, params, self._id_manager))
    for index, text in enumerate(self._inclusion_exclusion.exclusion):
      params = {'name': f'EXC{index+1}', 'label': f'Exclusion {index+1} ', 'description': '', 'text': text, 'category': exc, 'identifier': f'{index + 1}'}
      results.append(model_instance(EligibilityCriterion, params, self._id_manager))
    params = {'name': 'STUDY POP', 'label': 'Study Population', 'description': '', 'includesHealthySubjects': True, 'criteria': results}
    return model_instance(StudyDesignPopulation, params, self._id_manager)

  def _get_amendments(self):
    reason = []
    for item in [self._amendment.primary_reason, self._amendment.secondary_reason]:
      params = {'code': item['code'] , 'otherReason': item['other_reason']}
      reason.append(model_instance(StudyAmendmentReason, params, self._id_manager))
    params = {
      'number': '1', 
      'summary': self._amendment.summary, 
      'substantialImpact': self._amendment.safety_impact or self._amendment.robustness_impact, 
      'primaryReason': reason[0], 
      'secondaryReasons': [reason[1]], 
      'enrollments': [self._amendment.enrollment]
    }
    return [model_instance(StudyAmendment, params, self._id_manager)]

  def _document_version(self, study: Study) -> StudyProtocolDocumentVersion:
    return study.documentedBy.versions[0]
  
  def _double_link(self, items, prev, next):
    for idx, item in enumerate(items):
      if idx == 0:
        setattr(item, prev, None)
      else:
        the_id = getattr(items[idx-1], 'id')
        setattr(item, prev, the_id)
      if idx == len(items)-1:  
        setattr(item, next, None)
      else:
        the_id = getattr(items[idx+1], 'id')
        setattr(item, next, the_id)
  
 