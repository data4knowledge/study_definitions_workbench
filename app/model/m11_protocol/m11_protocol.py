#import re
#import dateutil.parser as parser
from app.model.raw_docx.raw_docx import RawDocx
#from app.model.raw_docx.raw_table import RawTable
from usdm_model.wrapper import Wrapper
from usdm_model.study import Study
from usdm_model.study_design import StudyDesign
from usdm_model.study_version import StudyVersion
from usdm_model.study_title import StudyTitle
from usdm_model.study_protocol_document import StudyProtocolDocument
from usdm_model.study_protocol_document_version import StudyProtocolDocumentVersion
#from usdm_model.code import Code
from usdm_model.study_identifier import StudyIdentifier
from usdm_model.organization import Organization
from usdm_model.address import Address
#from usdm_model.alias_code import AliasCode
from usdm_model.narrative_content import NarrativeContent
#from usdm_excel.id_manager import IdManager
#from usdm_excel.cdisc_ct_library import CDISCCTLibrary
#from usdm_excel.iso_3166 import ISO3166
from usdm_excel.globals import Globals
from uuid import uuid4
from usdm_info import __model_version__ as usdm_version, __package_version__ as system_version
from d4kms_generic import application_logger
#from app.utility.address_service import AddressService
from app.model.m11_protocol.m11_title_page import M11TitlePage
from app.model.m11_protocol.m11_utility import *

class M11Protocol():
  
  DIV_OPEN_NS = '<div xmlns="http://www.w3.org/1999/xhtml">'
  DIV_CLOSE = '</div>'
  ICH_HEADERS = [
    ('INTERNATIONAL COUNCIL FOR HARMONISATION OF TECHNICAL REQUIREMENTS FOR PHARMACEUTICALS FOR HUMAN USE', 'ich-m11-header-1'),
    ('ICH HARMONISED GUIDELINE', 'ich-m11-header-2'),
    ('Clinical electronic Structured Harmonised Protocol', 'ich-m11-header-3'),
    ('(CeSHarP)', 'ich-m11-header-4'),
    ('Example', 'ich-m11-header-4')
  ]
  DESIGN_ITEMS = [
    ('Number of Arms', 'ich-m11-overall-design-title'),
    ('Trial Blind Schema', 'ich-m11-overall-design-title'),
    ('Number of Participants', 'ich-m11-overall-design-title'),
    ('Duration', 'ich-m11-overall-design-title'),
    ('Committees', 'ich-m11-overall-design-title'),
    ('Blinded Roles', 'ich-m11-overall-design-title')
  ]

  def __init__(self, filepath, system_name, system_version):
    self._globals = Globals()
    self._globals.create()
    self._raw_docx = RawDocx(filepath)
    self._id_manager = self._globals.id_manager
    self._cdisc_ct_manager = self._globals.cdisc_ct_library
    self._system_name = system_name
    self._system_version = system_version
    self.sections = []
    self._title_page = M11TitlePage(self._raw_docx, self._system_name, self._system_version, self._globals)

  async def process(self):
    self._decode_ich_header()
    await self._title_page.process()
    self._decode_trial_design_summary()
    self._build_sections()

  def to_usdm(self) -> Wrapper:
    try:
      study = self._study(self._title_page.full_title)
      doc_version = self._document_version(study)
      root = model_instance(NarrativeContent, {'name': 'ROOT', 'sectionNumber': '0', 'sectionTitle': 'Root', 'text': '', 'childIds': [], 'previousId': None, 'nextId': None}, self._id_manager)
      doc_version.contents.append(root)
      local_index = self._sections(root, self.sections, 0, 1, doc_version)
      self._double_link(doc_version.contents, 'previousId', 'nextId')
      return Wrapper(study=study, usdmVersion=usdm_version, systemName=self._system_name, systemVersion=self._system_version).to_json()
    except Exception as e:
      application_logger.exception(f"Exception raised parsing M11 content. See logs for more details", e)
      return None

  def extra(self):
    return self._title_page.extra()
  
  def _decode_ich_header(self):
    section = self._raw_docx.target_document.section_by_ordinal(1)
    for header in self.ICH_HEADERS:
      items = section.find(header[0])
      for item in items:
        item.add_class(header[1])

  def _decode_trial_design_summary(self):
    section = self._raw_docx.target_document.section_by_number('1.1.2')
    tables = section.tables()
    table = tables[0]
    table.replace_class('ich-m11-table', 'ich-m11-overall-design-table')
    for design_item in self.DESIGN_ITEMS:
      items = section.find_at_start(design_item[0])
      for item in items:
        item.add_span(design_item[0], design_item[1])

  def _sections(self, parent, sections, index, level, doc_version) -> int:
    process = True
    previous = None
    local_index = index
    loop = 0
    while process:
      section = sections[local_index]
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
          local_index = self._sections(previous, sections, local_index, level + 1, doc_version)
        else:
          application_logger.error(f"No previous set processing sections")
          local_index += 1
      elif section.level < level: 
        return local_index
      if local_index >= len(sections):
        process = False
    return local_index
    
  def _study(self, title):
    sponsor_title_code = cdisc_ct_code('C99905x2', 'Official Study Title', self._cdisc_ct_manager, self._id_manager)
    protocl_status_code = cdisc_ct_code('C85255', 'Draft', self._cdisc_ct_manager, self._id_manager)
    intervention_model_code = cdisc_ct_code('C82639', 'Parallel Study', self._cdisc_ct_manager, self._id_manager)
    sponsor_code = cdisc_ct_code("C70793", 'Clinical Study Sponsor', self._cdisc_ct_manager, self._id_manager)
    study_title = model_instance(StudyTitle, {'text': title, 'type': sponsor_title_code}, self._id_manager)
    protocl_document_version = model_instance(StudyProtocolDocumentVersion, {'protocolVersion': '1', 'protocolStatus': protocl_status_code}, self._id_manager)
    protocl_document = model_instance(StudyProtocolDocument, {'name': 'PROTOCOL V1', 'label': '', 'description': '', 'versions': [protocl_document_version]}, self._id_manager)
    study_design = model_instance(StudyDesign, {'name': 'Study Design', 'label': '', 'description': '', 
      'rationale': 'XXX', 'interventionModel': intervention_model_code, 'arms': [], 'studyCells': [], 
      'epochs': [], 'population': None}, self._id_manager)
    sponsor_address = self._title_page.sponsor_address
    print(f"ADDRESS: {sponsor_address}")
    address = model_instance(Address, sponsor_address, self._id_manager)
    organization = model_instance(Organization, {'name': self._title_page.sponsor_name, 'organizationType': sponsor_code, 'identifier': "123456789", 'identifierScheme': "DUNS", 'legalAddress': address}, self._id_manager) 
    identifier = model_instance(StudyIdentifier, {'studyIdentifier': self._title_page.sponsor_protocol_identifier, 'studyIdentifierScope': organization}, self._id_manager)
    study_version = model_instance(StudyVersion, {'versionIdentifier': '1', 'rationale': 'XXX', 'titles': [study_title], 'studyDesigns': [study_design], 
                                                     'documentVersionId': protocl_document_version.id, 'studyIdentifiers': [identifier], 'studyPhase': self._title_page.trial_phase}, self._id_manager) 
    study = model_instance(Study, {'id': uuid4(), 'name': self._title_page.study_name, 'label': '', 'description': '', 'versions': [study_version], 'documentedBy': protocl_document}, self._id_manager) 
    return study

  def _document_version(self, study):
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
  
  def _build_sections(self):
    for section in self._raw_docx.target_document.sections:
      self.sections.append(section)
  