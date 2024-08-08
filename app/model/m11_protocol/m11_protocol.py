import re  
from app.model.raw_docx.raw_docx import RawDocx
from app.model.raw_docx.raw_table import RawTable
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
from usdm_model.alias_code import AliasCode
from usdm_model.narrative_content import NarrativeContent
from usdm_excel.id_manager import IdManager
from usdm_excel.cdisc_ct_library import CDISCCTLibrary
from uuid import uuid4
from usdm_info import __model_version__ as usdm_version, __package_version__ as system_version
from d4kms_generic import application_logger

class M11Protocol():
  
  DIV_OPEN_NS = '<div xmlns="http://www.w3.org/1999/xhtml">'
  DIV_CLOSE = '</div>'

  def __init__(self, filepath, system_name, system_version):
    self._raw_docx = RawDocx(filepath)
    self._id_manager = IdManager(application_logger)
    self._cdisc_ct_manager = CDISCCTLibrary(application_logger)
    self._system_name = system_name
    self._system_version = system_version
    self.sections = []
    self.acronym = None
    self.full_title = None
    self.sponsor_protocol_identifier = None
    self.original_protocol = None
    self.version_number = None
    self.amendment_identifier = None
    self.amendment_scope = None
    self.compound_codes = None
    self.compund_names = None
    self.trial_phase_raw = None
    self.trial_phase = None
    self.short_title = None
    self.sponsor_name_and_address = None
    self.sponsor_name = None
    self.sponsor_address = None
    self.regulatory_agency_identifiers = None
    self.sponsor_approval_date = None
    self._decode_title_page()
    self._build_sections()
    print(f"Titles {self.full_title}, {self.short_title}")

  def to_usdm(self) -> Wrapper:
    try:
      study = self._study(self.full_title)
      doc_version = self._document_version(study)
      root = self._model_instance(NarrativeContent, {'name': 'ROOT', 'sectionNumber': '0', 'sectionTitle': 'Root', 'text': '', 'childIds': [], 'previousId': None, 'nextId': None})
      doc_version.contents.append(root)
      local_index = self._sections(root, self.sections, 0, 1, doc_version)
      self._double_link(doc_version.contents, 'previousId', 'nextId')
      return Wrapper(study=study, usdmVersion=usdm_version, systemName=self._system_name, systemVersion=self._system_version).to_json()
    except Exception as e:
      application_logger.exception(f"Exception raised parsing M11 content. See logs for more details", e)
      return None

  def _decode_title_page(self):
    section = self._raw_docx.target_document.section_by_ordinal(1)
    tables = section.tables()
    table = tables[0]
    self.full_title = self._table_get_row(table, 'Full Title')
    self.acronym = self._table_get_row(table, 'Acronym')
    self.sponsor_protocol_identifier = self._table_get_row(table, 'Sponsor Protocol Identifier')
    self.original_protocol = self._table_get_row(table, 'Original Protocol')
    self.version_number = self._table_get_row(table, 'Version Number')
    self.amendment_identifier = self._table_get_row(table, 'Amendment Identifier')
    self.amendment_scope = self._table_get_row(table, 'Amendment Scope')
    self.compound_codes = self._table_get_row(table, 'Compound Code(s)')
    self.compund_names = self._table_get_row(table, 'Compound Name(s)')
    self.trial_phase_raw = self._table_get_row(table, 'Trial Phase')
    self.trial_phase = self._phase()
    self.short_title = self._table_get_row(table, 'Short Title')
    self.sponsor_name_and_address = self._table_get_row(table, 'Sponsor Name and Address')
    self.sponsor_name, self.sponsor_address = self._sponsor_name_and_address()
    self.regulatory_agency_identifiers = self._table_get_row(table, 'Regulatory Agency Identifier Number(s)')
    self.sponsor_approval_date = self._table_get_row(table, 'Sponsor Approval Date')

  def _sections(self, parent, sections, index, level, doc_version) -> int:
    process = True
    previous = None
    local_index = index
    loop = 0
    while process:
      section = sections[local_index]
      if section.level == level:
        sn = section.number if section.number else ''
        st = section.title if section.title else '-'
        nc_text = f"{self.DIV_OPEN_NS}{section.to_html()}{self.DIV_CLOSE}"
        nc = self._model_instance(NarrativeContent, {'name': f"NC-{sn}", 'sectionNumber': sn, 'sectionTitle': st, 'text': nc_text, 'childIds': [], 'previousId': None, 'nextId': None})
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
    sponsor_title_code = self._cdisc_ct_code('C99905x2', 'Official Study Title')
    protocl_status_code = self._cdisc_ct_code('C85255', 'Draft')
    intervention_model_code = self._cdisc_ct_code('C82639', 'Parallel Study')
    country_code = self._iso_country_code('DNK', 'Denmark')
    sponsor_code = self._cdisc_ct_code("C70793", 'Clinical Study Sponsor')
    study_title = self._model_instance(StudyTitle, {'text': title, 'type': sponsor_title_code})
    protocl_document_version = self._model_instance(StudyProtocolDocumentVersion, {'protocolVersion': '1', 'protocolStatus': protocl_status_code})
    protocl_document = self._model_instance(StudyProtocolDocument, {'name': 'PROTOCOL V1', 'label': '', 'description': '', 'versions': [protocl_document_version]})
    study_design = self._model_instance(StudyDesign, {'name': 'Study Design', 'label': '', 'description': '', 
      'rationale': 'XXX', 'interventionModel': intervention_model_code, 'arms': [], 'studyCells': [], 
      'epochs': [], 'population': None})
    address = self._model_instance(Address, {'line': 'Den Lille Havfrue', 'city': 'Copenhagen', 'district': '', 'state': '', 'postalCode': '12345', 'country': country_code})
    organization = self._model_instance(Organization, {'name': self.sponsor_name, 'organizationType': sponsor_code, 'identifier': "123456789", 'identifierScheme': "DUNS", 'legalAddress': address}) 
    identifier = self._model_instance(StudyIdentifier, {'studyIdentifier': self.sponsor_protocol_identifier, 'studyIdentifierScope': organization})
    study_version = self._model_instance(StudyVersion, {'versionIdentifier': '1', 'rationale': 'XXX', 'titles': [study_title], 'studyDesigns': [study_design], 
                                                     'documentVersionId': protocl_document_version.id, 'studyIdentifiers': [identifier], 'studyPhase': self.trial_phase}) 
    study = self._model_instance(Study, {'id': uuid4(), 'name': self._study_name(), 'label': '', 'description': '', 'versions': [study_version], 'documentedBy': protocl_document}) 
    return study

  def _cdisc_ct_code(self, code, decode):
    return self._model_instance(Code, {'code': code, 'decode': decode, 'codeSystem': self._cdisc_ct_manager.system, 'codeSystemVersion': self._cdisc_ct_manager.version})

  def _iso_country_code(self, code, decode):
    return self._model_instance(Code, {'code': 'code', 'decode': decode, 'codeSystem': 'ISO 3166 1 alpha3', 'codeSystemVersion': '2020-08'})
  
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
    for section in self._raw_docx.target_document.sections:
      self.sections.append(section)

  def _table_get_row(self, table: RawTable, key: str) -> str:
    for row in table.rows:
      if row.cells[0].is_text():
        if row.cells[0].text().upper().startswith(key.upper()):
          return row.cells[1].text().strip()
    return None

  def _sponsor_name_and_address(self):
    name = '[Sponsor Name]'
    address = '[Sponsor Address]'
    parts = self.sponsor_name_and_address.split('\n')
    if len(parts) > 0:
      name = parts[0].strip()
      application_logger.info(f"Sponsor name set to '{name}'")
    if len(parts) > 1:
      address = (',').join([x.strip() for x in parts[1:]])
    return name, address

  def _study_name(self):
    items = [self.acronym, self.sponsor_protocol_identifier, self.compound_codes]
    for item in items:
      if item:
        name = re.sub('[\W_]+', '', item.upper())
        application_logger.info(f"Study name set to '{name}'")
        return name
    return ''  
  
  def _phase(self):
    phase_map = [
      (['0', 'PRE-CLINICAL', 'PRE CLINICAL'], {'code': 'C54721',  'decode': 'Phase 0 Trial'}),
      (['1', 'I'],                            {'code': 'C15600',  'decode': 'Phase I Trial'}),
      (['1-2'],                               {'code': 'C15693',  'decode': 'Phase I/II Trial'}),
      (['1/2/3'],                             {'code': 'C198366', 'decode': 'Phase I/II/III Trial'}),
      (['1/3'],                               {'code': 'C198367', 'decode': 'Phase I/III Trial'}),
      (['1A', 'IA'],                          {'code': 'C199990', 'decode': 'Phase Ia Trial'}),
      (['1B', 'IB'],                          {'code': 'C199989', 'decode': 'Phase Ib Trial'}),
      (['2', 'II'],                           {'code': 'C15601',  'decode': 'Phase II Trial'}),
      (['2-3', 'II-III'],                     {'code': 'C15694',  'decode': 'Phase II/III Trial'}),
      (['2A', 'IIA'],                         {'code': 'C49686',  'decode': 'Phase IIa Trial'}),
      (['2B', 'IIB'],                         {'code': 'C49688',  'decode': 'Phase IIb Trial'}),
      (['3', 'III'],                          {'code': 'C15602',  'decode': 'Phase III Trial'}),
      (['3A', 'IIIA'],                        {'code': 'C49687',  'decode': 'Phase IIIa Trial'}),
      (['3B', 'IIIB'],                        {'code': 'C49689',  'decode': 'Phase IIIb Trial'}),
      (['4', 'IV'],                           {'code': 'C15603',  'decode': 'Phase IV Trial'}),
      (['5', 'V'],                            {'code': 'C47865',  'decode': 'Phase V Trial'})
    ]
    phase = self.trial_phase_raw.upper().replace('PHASE', '').strip()
    #print(f"PHASE1: {phase}")
    for tuple in phase_map:
      #print(f"PHASE2: {tuple}")
      if phase in tuple[0]:
        entry = tuple[1]
        cdisc_phase_code = self._cdisc_ct_code(entry['code'], entry['decode'])
        application_logger.info(f"Trial phase '{phase}' decoded as '{entry['code']}', '{entry['decode']}'")
        return self._model_instance(AliasCode, {'standardCode': cdisc_phase_code})
    cdisc_phase_code = self._cdisc_ct_code('C48660', '[Trial Phase] Not Applicable')
    application_logger.warning(f"Trial phase '{phase}' not decoded")
    return self._model_instance(AliasCode, {'standardCode': cdisc_phase_code})





