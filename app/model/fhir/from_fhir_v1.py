from usdm_model.wrapper import Wrapper
from usdm_model.study import Study
from usdm_model.study_design import StudyDesign
from usdm_model.study_version import StudyVersion
from usdm_model.study_title import StudyTitle
from usdm_model.study_protocol_document import StudyProtocolDocument
from usdm_model.study_protocol_document_version import StudyProtocolDocumentVersion
from usdm_model.code import Code
from usdm_model.alias_code import AliasCode
from usdm_model.study_identifier import StudyIdentifier
from usdm_model.organization import Organization
from usdm_model.address import Address
from usdm_model.narrative_content import NarrativeContent
from usdm_db.errors_and_logging.errors_and_logging import ErrorsAndLogging
from usdm_excel.id_manager import IdManager
from usdm_excel.cdisc_ct_library import CDISCCTLibrary
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.composition import Composition, CompositionSection
from usdm_info import __model_version__ as usdm_version, __package_version__ as system_version
from app import SYSTEM_NAME, VERSION
from app.model.file_handling.data_files import DataFiles
from app.model.fhir.fhir_title_page import FHIRTitlePage
from d4kms_generic.logger import application_logger

class FromFHIRV1():

  class LogicError(Exception):
    pass

  def __init__(self, uuid: str):
    self._errors_and_logging = ErrorsAndLogging()
    self._id_manager = IdManager(self._errors_and_logging)
    self._cdisc_ct_manager = CDISCCTLibrary(self._errors_and_logging)
    self._uuid = uuid
    self._ncs = []
    
  def to_usdm(self) -> str:
    try:
      files = DataFiles(self._uuid)
      data = files.read('fhir')
      study = self._from_fhir(self._uuid, data)
      return Wrapper(study=study, usdmVersion=usdm_version, systemName=SYSTEM_NAME, systemVersion=VERSION).to_json()
    except Exception as e:
      self._errors_and_logging.exception(f"Exception raised parsing FHIR content. See logs for more details", e)
      return None
  
  def _from_fhir(self, uuid: str, data: str) -> Wrapper:
    bundle = Bundle.parse_raw(data)
    protocol_document = self._document(bundle)
    study = self._study(protocol_document)
    return study

  def _document(self, bundle):
    self._ncs = []
    protocl_status_code = self._cdisc_ct_code('C85255', 'Draft')
    protocl_document_version = self._model_instance(StudyProtocolDocumentVersion, {'protocolVersion': '1', 'protocolStatus': protocl_status_code})
    protocl_document = self._model_instance(StudyProtocolDocument, {'name': 'PROTOCOL V1', 'label': '', 'description': '', 'versions': [protocl_document_version]})
    root = self._model_instance(NarrativeContent, {'name': 'ROOT', 'sectionNumber': '0', 'sectionTitle': 'Root', 'text': '', 'childIds': [], 'previousId': None, 'nextId': None})
    protocl_document_version.contents.append(root)
    for item in bundle.entry[0].resource.section:
      nc = self._section(item, protocl_document_version)
      root.childIds.append(nc.id)
    self._double_link(protocl_document_version.contents, 'previousId', 'nextId')
    #print(f"DOC: {protocl_document}")
    return protocl_document

  def _section(self, section: CompositionSection, protocol_document_version: StudyProtocolDocumentVersion):
    #print(f"SECTION: {section.title}, {section.code.text}")
    section_number = self._get_section_number(section.code.text)
    #print(f"SECTION NUMBER: {section.code.text} -> {section_number}")
    nc = self._model_instance(NarrativeContent, {'name': f"{section.code.text}", 'sectionNumber': section_number, 'sectionTitle': section.title, 'text': section.text.div, 'childIds': [], 'previousId': None, 'nextId': None})
    protocol_document_version.contents.append(nc)
    if section.section:
      for item in section.section:
        child_nc = self._section(item, protocol_document_version)
        nc.childIds.append(child_nc.id)
    return nc

  def _get_section_number(self, text):
    parts = text.split('-')
    return parts[0].replace('section', '') if len(parts) >= 2 else ''
      
  def _study(self, protocol_document: StudyProtocolDocument):
    protocol_document_version = protocol_document.versions[0]
    #print(f"PDV: {protocol_document_version}")
    sections = protocol_document_version.contents
    #print(f"SECTION: {protocol_document_version}")
    title_page = FHIRTitlePage(sections[1].text)
    sponsor_title_code = self._cdisc_ct_code('C99905x2', 'Official Study Title')
    study_title = self._model_instance(StudyTitle, {'text': title_page.full_title, 'type': sponsor_title_code})
    protocl_status_code = self._cdisc_ct_code('C85255', 'Draft')
    intervention_model_code = self._cdisc_ct_code('C82639', 'Parallel Study')
    country_code = self._iso_country_code('DNK', 'Denmark')
    sponsor_code = self._cdisc_ct_code("C70793", 'Clinical Study Sponsor')
    #protocol_document_version = self._model_instance(StudyProtocolDocumentVersion, {'protocolVersion': title_page.version_number, 'protocolStatus': protocl_status_code})
    #protocol_document = self._model_instance(StudyProtocolDocument, {'name': f'PROTOCOL_DOCUMENT', 'label': f'Protocol Document', 'description': 'The protocol document for the study', 'versions': [protocol_document_version]})
    study_design = self._model_instance(StudyDesign, {'name': 'Study Design', 'label': '', 'description': '', 
      'rationale': '[Not Found]', 'interventionModel': intervention_model_code, 'arms': [], 'studyCells': [], 
      'epochs': [], 'population': None})
    address = self._model_instance(Address, {'line': 'Den Lille Havfrue', 'city': 'Copenhagen', 'district': '', 'state': '', 'postalCode': '12345', 'country': country_code})
    organization = self._model_instance(Organization, {'name': title_page.sponsor_name, 'organizationType': sponsor_code, 'identifier': "123456789", 'identifierScheme': "DUNS", 'legalAddress': address}) 
    identifier = self._model_instance(StudyIdentifier, {'studyIdentifier': title_page.sponsor_protocol_identifier, 'studyIdentifierScope': organization})
    study_version = self._model_instance(StudyVersion, {'versionIdentifier': title_page.version_number, 'rationale': 'XXX', 'titles': [study_title], 'studyDesigns': [study_design], 
                                                     'documentVersionId': protocol_document_version.id, 'studyIdentifiers': [identifier], 'studyPhase': self._phase(title_page.trial_phase)}) 
    study = self._model_instance(Study, {'id': self._uuid, 'name': 'Study', 'label': '', 'description': '', 'versions': [study_version], 'documentedBy': protocol_document}) 
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

  def _phase(self, raw_phase):
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
    phase = raw_phase.upper().replace('PHASE', '').strip()
    for tuple in phase_map:
      if phase in tuple[0]:
        entry = tuple[1]
        cdisc_phase_code = self._cdisc_ct_code(entry['code'], entry['decode'])
        application_logger.info(f"Trial phase '{phase}' decoded as '{entry['code']}', '{entry['decode']}'")
        return self._model_instance(AliasCode, {'standardCode': cdisc_phase_code})
    cdisc_phase_code = self._cdisc_ct_code('C48660', '[Trial Phase] Not Applicable')
    application_logger.warning(f"Trial phase '{phase}' not decoded")
    return self._model_instance(AliasCode, {'standardCode': cdisc_phase_code})





