import json
import warnings
from model.file_import import FileImport
from model.files import Files
from model.version import Version
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from usdm_db import USDMDb

class USDMJson():

  def __init__(self, id: int, session: Session):
    self.id = id
    version = Version.find(id, session)
    file_import = FileImport.find(version.import_id, session)
    self.uuid = file_import.uuid
    self.type = file_import.type
    self.m11 = True if self.type == "DOCX" else False
    self._files = Files(file_import.uuid)
    fullpath, filename = self._files.path('usdm')
    data = open(fullpath)
    self._data = json.load(data)

  def fhir(self):
    data = self.fhir_data()
    fullpath, filename = self._files.save("fhir", data)
    return fullpath, filename, 'text/plain' 

  def fhir_data(self):
    usdm = USDMDb()
    usdm.from_json(self._data)
    return usdm.to_fhir()

  def pdf(self):
    usdm = USDMDb()
    usdm.from_json(self._data)
    data = usdm.to_pdf()
    fullpath, filename = self._files.save("protocol", data)
    return fullpath, filename, 'text/plain' 

  def study_version(self):
    version = self._data['study']['versions'][0]
    result = {
      'id': self.id,
      'version_identifier': version['versionIdentifier'],
      'identifiers': {},
      'titles': {},
      'study_designs': {},
      'phase': ''
    }
    for identifier in version['studyIdentifiers']:
      result['identifiers'][identifier['studyIdentifierScope']['organizationType']['decode']] = identifier
    for title in version['titles']:
      result['titles'][title['type']['decode']] = title['text']
    for design in version['studyDesigns']:
      result['study_designs'][design['id']] = {'id': design['id'], 'name': design['name'], 'label': design['label']}
    result['phase'] = version['studyPhase']
    return result

  def study_design_overall_parameters(self, id: str):
    version = self._data['study']['versions'][0]
    design = self._study_design(id)
    if design:
      result = {
        'id': self.id,
        'intervention_model': None,
        'population_type':  None,
        'population_condition': '[Population Condition]',
        'population_age':  None,
        'control_type': '[Control Type]',
        'control_description': '[Control Description]',
        'master_protocol': 'Yes' if len(version['studyDesigns']) > 1 else 'No',
        'adaptive_design': 'No',
        'intervention_method': '[Intervention Assignment Method]',
        'site_distribution': '[Site Distribution and Geographic Scope]',
        'drug_device_indication': '[Drug / Device Combination Product Indication]'
      }
      # result['trial_types'] = self._set_trial_types(id)
      # result['trial_intent'] = self._set_trial_intent_types(id)
      result['intervention_model'] = design['interventionModel']['decode'] if design['interventionModel'] else '[Intervention Model]'
      result['population_age'] = self._population_age(design) if design['population'] else {'min': 0, 'max': 0, 'unit': ''}
      result['population_type'] = 'Adult' if result['population_age']['min'] >= 18 else 'Child'
      result['characteristics'] = self._set_characteristics(id)
      if "ADAPTIVE" in result['characteristics']:
        result['adaptive_design'] = 'Yes'
      return result
    else:
      return None

  def study_design_design_parameters(self, id: str):
    design = self._study_design(id)
    if design:
      result = {
        'id': self.id,
        'arms': None,
        'trial_blind_scheme': None,
        'blinded_roles': None,
        'participants': None,
        'duration': '[Duration]',
        'independent_committee': '[Independent Committee]'
      }
      result['arms'] = len(design['arms']) if design['arms'] else '[Arms]'
      result['trial_blind_scheme'] = design['blindingSchema']['standardCode']['decode'] if design['blindingSchema'] else '[Trial Blind Schema]'
      result['blinded_roles'] = self._set_blinded_roles(id)
      result['participants'] = self._population_recruitment(design) if design['population'] else {'enroll': 0, 'complete': 0}
      return result
    else:
      return None

  def _set_blinded_roles(self, id) -> dict:
    design = self._study_design(id)
    result = {}
    if design['maskingRoles']:
      for item in design['maskingRoles']:
        result[item['role']['decode']] = item['role']['decode']
    else:
      result['[Blinded Roles]'] = '[Blinded Roles]'
    return result

  def _set_characteristics(self, id) -> dict:
    return self._set_multiple(id, 'characteristics', '[Characteristics]')

  def _set_trial_intent_types(self, id) -> dict:
    return self._set_multiple(id, 'trialIntentTypes', '[Trial Intent]')

  def _set_trial_types(self, id) -> dict:
    return self._set_multiple(id, 'trialTypes', '[Trial TYpes]')

  def _set_multiple(self, id: str, collection: str, missing: str) -> dict:
    design = self._study_design(id)
    result = {}
    if design[collection]:
      for item in design[collection]:
        result[item['decode']] = item['decode']
    else:
      result[missing] = missing
    return result

  def study_design_schema(self, id: str):
    design = self._study_design(id)
    if design:
      section = self._section_by_number("1.2") if self.m11 else self._section_by_title_contains("study design")
      return self._image_in_section(section) if section else '[Study Design]'

  def study_design_interventions(self, id: str):
    design = self._study_design(id)
    if design:
      section = self._section_by_number("6.1") if self.m11 else self._section_by_title_contains("Trial Interventions")
      return section['text'] if section else '[Trial Interventions]'

  def study_design_estimands(self, id: str):
    design = self._study_design(id)
    if design:
      section = self._section_by_number("3.1") if self.m11 else self._section_by_title_contains("Primary Objective")
      return section['text'] if section else '[Estimands]'

  def _image_in_section(self, section):
    soup = self._get_soup(section['text'])
    for ref in soup(['img']):
      return ref
    return ""

  def _section_by_number(self, number):
    document = self._document()
    if document:
      return next((x for x in document['contents'] if x['sectionNumber'] == number), None)
    return None

  def _section_by_title_contains(self, title):
    document = self._document()
    if document:
      return next((x for x in document['contents'] if title.upper() in x['sectionTitle'].upper()), None)
    return None

  def _study_design(self, id: str):
    version = self._data['study']['versions'][0]
    return next((x for x in version['studyDesigns'] if x['id'] == id), None)
  
  def _document(self):
    version = self._data['study']['versions'][0]
    id = version['documentVersionId']
    return next((x for x in self._data['study']['documentedBy']['versions'] if x['id'] == id), None)

  def _get_soup(self, text: str):
    try:
      with warnings.catch_warnings(record=True) as warning_list:
        result =  BeautifulSoup(text, 'html.parser')
      if warning_list:
        pass
        #for item in warning_list:
        #  errors_and_logging.debug(f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'")
      return result
    except Exception as e:
      #errors_and_logging.exception(f"Parsing '{text}' with soup", e)
      return None

  def _population_age(self, study_design: dict) -> dict:
    population = study_design['population']
    result = self._min_max(population['plannedAge'])
    for cohort in population['cohorts']:
      cohort = self._min_max(population['plannedAge'])
      if cohort['min'] < result['min']:
        result['min'] = cohort['min']
      if cohort['max'] > result['max']:
        result['max'] = cohort['max']
    return result

  def _min_max(self, item):
    print(f"ITEM: {item}")
    return {'min': int(item['minValue']), 'max': int(item['maxValue']), 'unit': item['unit']['decode']} if item else {'min': 100, 'max': 0, 'unit': 'Year'}

  def _population_recruitment(self, study_design: dict) -> dict:
    population = study_design['population']
    enroll = population['plannedEnrollmentNumber']
    complete = population['plannedCompletionNumber']
    return {'enroll': int(enroll['maxValue']), 'complete': int(complete['maxValue'])} if enroll and complete else {'enroll': 0, 'complete': '0'}
