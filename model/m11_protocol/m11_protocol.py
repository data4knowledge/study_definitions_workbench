from model.raw_docx.raw_docx import RawDocx
from model.raw_docx.raw_table import RawTable
from usdm_model.wrapper import Wrapper
from usdm_model.study import Study
from usdm_model.study_design import StudyDesign
from usdm_model.study_version import StudyVersion
from usdm_model.study_title import StudyTitle
from usdm_model.study_protocol_document import StudyProtocolDocument
from usdm_model.study_protocol_document_version import StudyProtocolDocumentVersion
from usdm_model.code import Code
from usdm_model.study_identifier import StudyIdentifier
from usdm_model.organization import Organization
from usdm_model.address import Address
from usdm_model.narrative_content import NarrativeContent
from usdm_excel.id_manager import IdManager
from usdm_excel.cdisc_ct_library import CDISCCTLibrary
from uuid import uuid4
from usdm_info import __model_version__ as usdm_version, __package_version__ as system_version
from d4kms_generic import application_logger

class M11Protocol():
  
  DIV_OPEN_NS = '<div xmlns="http://www.w3.org/1999/xhtml">'
  DIV_CLOSE = '</div>'

  def __init__(self, filepath):
    docx = RawDocx(filepath)
    self._id_manager = IdManager(application_logger)
    self._cdisc_ct_manager = CDISCCTLibrary(application_logger)
    self.raw = docx.target_document
    self.sections = []
    self.full_title = None
    self.sponsor_protocol_identifier = None
    self.original_protocol = None
    self.version_number = None
    self.amendment_identifier = None
    self.amendment_scope = None
    self.compound_codes = None
    self.compund_names = None
    self.trial_phase_raw = None
    self.short_title = None
    self.sponsor_name_and_address = None
    self.regulatory_agency_identifiers = None
    self.sponsor_approval_date = None
    self._decode_title_page()
    self._build_sections()
    #print(f"Titles {self.full_title}, {self.short_title}")

  def to_usdm(self) -> Wrapper:
    try:
      study = self._study(self.m11.full_title)
      doc_version = self._document_version(study)
      root = self._model_instance(NarrativeContent, {'name': 'ROOT', 'sectionNumber': '0', 'sectionTitle': 'Root', 'text': '', 'childIds': [], 'previousId': None, 'nextId': None})
      doc_version.contents.append(root)
      local_index = self._sections(root, self.m11.sections, 0, 1, doc_version)
      self._double_link(doc_version.contents, 'previousId', 'nextId')
      return Wrapper(study=study, usdmVersion=usdm_version, systemName=self.SYSTEM_NAME, systemVersion=system_version)
    except Exception as e:
      application_logger.exception(f"Exception raised parsing M11 content. See logs for more details", e)
      return None

  def _decode_title_page(self):
    section = self.raw.section_by_ordinal(1)
    tables = section.tables()
    table = tables[0]
    self.full_title = self._table_get_row(table, 'Full Title')
    self.sponsor_protocol_identifier = self._table_get_row(table, 'Sponsor Protocol Identifier')
    self.original_protocol = self._table_get_row(table, 'Original Protocol')
    self.version_number = self._table_get_row(table, 'Version Number')
    self.amendment_identifier = self._table_get_row(table, 'Amendment Identifier')
    self.amendment_scope = self._table_get_row(table, 'Amendment Scope')
    self.compound_codes = self._table_get_row(table, 'Compound Code(s)')
    self.compund_names = self._table_get_row(table, 'Compound Name(s)')
    self.trial_phase_raw = self._table_get_row(table, 'Trial Phase')
    self.short_title = self._table_get_row(table, 'Short Title')
    self.sponsor_name_and_address = self._table_get_row(table, 'Sponsor Name and Address')
    self.regulatory_agency_identifiers = self._table_get_row(table, 'Regulatory Agency Identifier Number(s)')
    self.sponsor_approval_date = self._table_get_row(table, 'Sponsor Approval Date')

  def _sections(self, parent, sections, index, level, doc_version) -> int:
    process = True
    previous = None
    local_index = index
    loop = 0
    while process:
      #loop += 1
      #if loop > 400:
      #  process = False
      section = sections[local_index]
      #print(f"INDEX: {local_index} {section.level} {level}")
      if section.level == level:
        #print(f"INDEX: EQ")
        sn = section.number if section.number else ''
        st = section.title if section.title else '-'
        nc_text = f"{self.DIV_OPEN_NS}{section.to_html()}{self.DIV_CLOSE}"
        #print(f"NC: {nc_text}")
        nc = self._model_instance(NarrativeContent, {'name': f"NC-{sn}", 'sectionNumber': sn, 'sectionTitle': st, 'text': nc_text, 'childIds': [], 'previousId': None, 'nextId': None})
        #print(f"NC: {nc.text}")
        doc_version.contents.append(nc)
        parent.childIds.append(nc.id)
        previous = nc
        local_index += 1
      elif section.level > level: 
        #print(f"INDEX: GT")
        if previous:
          local_index = self._sections(previous, sections, local_index, level + 1, doc_version)
        else:
          application_logger.error(f"No previous set processing sections")
          local_index += 1
      elif section.level < level: 
        #print(f"INDEX: LT")
        return local_index
      if local_index >= len(sections):
        process = False
    return local_index
    
  def _study(self, title):
    sponsor_title_code = self._cdisc_ct_code('C99905x2', 'Official Study Title')
    protocl_status_code = self._cdisc_ct_code('C85255', 'Draft')
    intervention_model_code = self._cdisc_ct_code('C82639', 'Parallel Study')
    country_code = self._iso_country_code('DNK', 'Denmark')
    sponsor_code = self._cdisc_ct_code("C70793", '"Clinical Study Sponsor')
    study_title = self._model_instance(StudyTitle, {'text': title, 'type': sponsor_title_code})
    protocl_document_version = self._model_instance(StudyProtocolDocumentVersion, {'protocolVersion': '1', 'protocolStatus': protocl_status_code})
    protocl_document = self._model_instance(StudyProtocolDocument, {'name': 'PROTOCOL V1', 'label': '', 'description': '', 'versions': [protocl_document_version]})
    study_design = self._model_instance(StudyDesign, {'name': 'Study Design', 'label': '', 'description': '', 
      'rationale': 'XXX', 'interventionModel': intervention_model_code, 'arms': [], 'studyCells': [], 
      'epochs': [], 'population': None})
    address = self._model_instance(Address, {'line': 'Den Lille Havfrue', 'city': 'Copenhagen', 'district': '', 'state': '', 'postalCode': '12345', 'country': country_code})
    organization = self._model_instance(Organization, {'name': 'Sponsor', 'organizationType': sponsor_code, 'identifier': "123456789", 'identifierScheme': "DUNS", 'legalAddress': address}) 
    identifier = self._model_instance(StudyIdentifier, {'studyIdentifier': 'SPONSOR-1234', 'studyIdentifierScope': organization})
    study_version = self._model_instance(StudyVersion, {'versionIdentifier': '1', 'rationale': 'XXX', 'titles': [study_title], 'studyDesigns': [study_design], 
                                                     'documentVersionId': protocl_document_version.id, 'studyIdentifiers': [identifier]}) 
    study = self._model_instance(Study, {'id': uuid4(), 'name': 'Study', 'label': '', 'description': '', 'versions': [study_version], 'documentedBy': protocl_document}) 
    return study

  def _cdisc_ct_code(self, code, decode):
    return self._model_instance(Code, {'code': code, 'decode': decode, 'codeSystem': self._cdisc_ct_manager.system, 'codeSystemVersion': self._cdisc_ct_manager.version})

  def _iso_country_code(self, code, decode):
    return self._model_instance(Code, {'code': code, 'decode': decode, 'codeSystem': 'ISO 3166 1 alpha3', 'codeSystemVersion': '2020-08'})
  
  def _document_version(self, study):
    return study.documentedBy.versions[0]
  
  def _model_instance(self, cls, params):
    params['id'] = params['id'] if 'id' in params else self._id_manager.build_id(cls)
    params['instanceType'] = cls.__name__
    return cls(**params)
  
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
    for section in self.raw.sections:
      self.sections.append(section)

  def _table_get_row(self, table: RawTable, key: str) -> str:
    for row in table.rows:
      if row.cells[0].is_text():
        if row.cells[0].text().upper().startswith(key.upper()):
          return row.cells[1].text().strip()
    return None
