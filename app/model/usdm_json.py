import json
import yaml
import warnings
from app.model.file_import import FileImport
from app.model.files import Files
from app.model.fhir.to_fhir_v1 import ToFHIRV1
from app.model.fhir.to_fhir_v2 import ToFHIRV2
from app.model.version import Version
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from usdm_db import USDMDb
from usdm_model import StudyDesign, Estimand

class USDMJson():

  def __init__(self, id: int, session: Session):
    self.id = id
    version = Version.find(id, session)
    file_import = FileImport.find(version.import_id, session)
    self.uuid = file_import.uuid
    self.type = file_import.type
    self.m11 = True if self.type == "DOCX" or self.type == "FHIR V1" else False
    self._files = Files(file_import.uuid)
    self._data = self._get_usdm()
    self._extra = self._get_extra()

  def fhir(self, version='1'):
    data = self.fhir_data(version)
    fullpath, filename = self._files.save("fhir", data)
    return fullpath, filename, 'text/plain' 

  def fhir_data(self, version='1'):
    return self.fhir_v2_data() if version.upper() == '2' else self.fhir_v1_data()

  def fhir_v1_data(self):
    #print(f"FHIR: VER 1 DATA")
    usdm = USDMDb()
    usdm.from_json(self._data)
    study = usdm.wrapper().study
    fhir = ToFHIRV1(study, self.uuid, self._extra)
    return fhir.to_fhir()

  def fhir_v2_data(self):
    #print(f"FHIR: VER 2 DATA")
    usdm = USDMDb()
    usdm.from_json(self._data)
    study = usdm.wrapper().study
    fhir = ToFHIRV2(study, self.uuid, self._extra)
    data = fhir.to_fhir()
    self._files.save('fhir_v2', data)
    return data

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
      section = None
      if self.m11:
        section = self._section_by_number("1.1.2")
      if not section:
        section = self._section_by_title_contains("Overall Design")
      result = {
        'id': self.id,
        'm11': self.m11,
        'text': section['text'] if section else '[Overall Parameters]',
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
        'm11': self.m11,
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

  def study_design_schema(self, id: str):
    design = self._study_design(id)
    if design:
      section = None
      if self.m11:
        section = self._section_by_number("1.2") 
      if not section:
        section = self._section_by_title_contains("trial schema")  
      if not section:
        section = self._section_by_title_contains("study design")
      return self._image_in_section(section) if section else '[Study Design]'
    else:
      return None
    
  def study_design_interventions(self, id: str):
    design = self._study_design(id)
    if design:
      section = None
      if self.m11:
        section = self._section_by_number("6.1")
      if not section:
        section = self._section_by_title_contains("Trial Intervention")
      if not section:
        section = self._section_by_title_contains("Intervention")
      result = {
        'id': self.id,
        'm11': self.m11,
        'interventions': [],
        'text': section['text'] if section else '[Trial Interventions]'
      }
      for intervention in design['studyInterventions']:
        print(f"R1:")
        record = {}
        record['arm'] = self._arm_from_intervention(design, intervention['id'])
        record['intervention'] = intervention
        result['interventions'].append(record)
      #print(f"INTERVENTIONS: {result}")
      return result
    else:
      return None

  def study_design_estimands(self, id: str):
    design = self._study_design(id)
    #print(f"ESTIMANDS: {'design' if design else ''}")
    if design:
      section = None
      if self.m11:
        section = self._section_by_number("3.1")
      if not section:
        section = self._section_by_title_contains("Primary Objective")
      result = {
        'id': self.id,
        'm11': self.m11,
        'estimands': [],
        'text': section['text'] if section else '[Estimands]'
      }
      for estimand in design['estimands']:
        record = {}
        #print(f"R1:")
        record['treatment'] = self._intervention(design, estimand['interventionId'])
        record['summary_measure'] = estimand['summaryMeasure']
        record['analysis_population'] = estimand['analysisPopulation']
        record['intercurrent_events'] = estimand['intercurrentEvents']
        record['objective'], record['endpoint'] = self._objective_endpoint_from_estimand(design, estimand['variableOfInterestId'])
        result['estimands'].append(record)
      #print(f"ESTIMANDS: {result}")
      return result
    else:
      return None

  def sample_size(self, id: str) -> dict:
    return self._section_response(id, '10.11', 'sample size', '[Sample Size]')
  
  def analysis_sets(self, id: str) -> dict:
    return self._section_response(id, '10.2', 'analysis sets', '[Analysis Sets]')

  def analysis_objectives(self, id: str) -> dict:
    return self._section_response(id, '10.4', 'analysis associated with primary', '[Analysis Associated with the Primary Objectives]')

  def adverse_events_special_interest(self, id: str) -> dict:
    return self._section_response(id, '9.3.2', 'adverse events of special interest', '[Adverse Events of Special Interest]')

  def safety_assessments(self, id: str) -> dict:
    return self._section_response(id, '8.4', 'safety assessments and procedures', '[Safety Assessment and Procedures]')

  def protocol_sections_list(self):
    sections = self.protocol_sections()
    result = []
    for section in sections:
      if (section['sectionNumber'] and section['sectionNumber'] != '0') and section['sectionTitle']:
        result.append({'section_number': section['sectionNumber'], 'section_title': section['sectionTitle']})
    return result

  def protocol_sections(self):
    document = self._document()
    if document:
      #print("A")
      sections = []
      narrative_content = self._first_narrative_content(document)
      #print(f"B {narrative_content}")
      while narrative_content:
        sections.append(narrative_content)
        narrative_content = self._find_narrative_content(document, narrative_content['nextId'])
      return sections
    return None

  def section(self, id):
    document = self._document()
    if document:
      narrative_content = self._find_narrative_content(document, id)
      narrative_content['heading'], narrative_content['level'] = self._format_heading(narrative_content)
      return narrative_content
    return None

  def _section_response(self, id: str, number: str, title: str, default: str) -> dict:
    design = self._study_design(id)
    if design and self.m11:
      return {
        'id': self.id,
        'm11': self.m11,
        'text': self._section_full_text(number, title, default)
      }
    return None

  def _section_full_text(self, number: str, title: str, default: str) -> str:
    section = None
    document = self._document()
    if document:
      section = self._section_by_number(number) 
      if not section:
        section = self._section_by_title_contains(title)
      if section:
        text = []
        process = True
        top_level = self._get_level(section)
        while process:
          print(f"SECTION: {section}")
          heading, level = self._format_heading(section)
          text.append(heading)
          text.append(section['text'])
          section = self._find_narrative_content(document, section['nextId'])
          process = True if self._get_level(section) > top_level else False
    return ('').join(text) if section else default

  def _get_number(self, narrative_content: dict):
    try:
      return int(narrative_content['sectionNumber'])
    except Exception as e:
      return 0
    
  def _get_level(self, narrative_content: dict):
    section_number = narrative_content['sectionNumber']
    if section_number.lower().startswith("appendix"):
      result = 1
    else:
      text = section_number[:-1] if section_number.endswith('.') else section_number
      result = len(text.split('.'))
    return result
  
  def _format_heading(self, narrative_content):
    level = self._get_level(narrative_content)
    number = narrative_content['sectionNumber']
    title = narrative_content['sectionTitle']
    if number and number == '0':
      return '', level
    elif number and title:
      return f'<h{level}>{number} {title}</h{level}>', level
    elif number:
      return f'<h{level}>{number}</h{level}>', level
    elif title:
      return f'<h{level}>{title}</h{level}>', level
    else:
      return '', level
    
  def _first_narrative_content(self, document: dict) -> dict:
    return next((x for x in document['contents'] if not x['previousId'] and x['nextId']), None)

  def _find_narrative_content(self, document: dict, id: str) -> dict:
    return next((x for x in document['contents'] if x['id'] == id), None)

  def _intervention(self, study_design: dict, intervention_id: str) -> dict:
    return next((x for x in study_design['studyInterventions'] if x['id'] == intervention_id), None)

  def _objective_endpoint_from_estimand(self, study_design: dict, variable_of_interest_id: str) -> dict:
    for objective in study_design['objectives']:
      endpoint = self._endpoint_from_objective(objective, variable_of_interest_id)
      if endpoint:
        return objective, endpoint
    return None, None
  
  def _endpoint_from_objective(self, objective: list, endpoint_id: str) -> dict:
    return next((x for x in objective['endpoints'] if x['id'] == endpoint_id), None)

  def _arm_from_intervention(self, study_design: dict, intervention_id: str) -> dict:
    element = next((x for x in study_design['studyInterventions'] if x['id'] == intervention_id), None)
    if element:
      cell = next((x for x in study_design['studyCells'] if intervention_id in x['elementIds']), None)
      if cell:
        return next((x for x in study_design['arms'] if x['id'] == cell['id']), None)
    return {'label': '[Not Found]', 'type': {'decode': '[Not Found]'}}
  
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

  def _image_in_section(self, section):
    soup = self._get_soup(section['text'])
    for ref in soup(['img']):
      return ref
    return ""

  def _section_by_number(self, number) -> dict:
    document = self._document()
    if document:
      return next((x for x in document['contents'] if x['sectionNumber'] == number), None)
    return None

  def _section_by_title_contains(self, title) -> dict:
    document = self._document()
    if document:
      return next((x for x in document['contents'] if title.upper() in x['sectionTitle'].upper()), None)
    return None

  def _study_design(self, id: str) -> dict:
    version = self._data['study']['versions'][0]
    return next((x for x in version['studyDesigns'] if x['id'] == id), None)
  
  def _document(self) -> dict:
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

  def _min_max(self, item) -> dict:
    #print(f"ITEM: {item}")
    return {'min': int(item['minValue']), 'max': int(item['maxValue']), 'unit': item['unit']['decode']} if item else {'min': 100, 'max': 0, 'unit': 'Year'}

  def _population_recruitment(self, study_design: dict) -> dict:
    population = study_design['population']
    enroll = population['plannedEnrollmentNumber']
    complete = population['plannedCompletionNumber']
    return {'enroll': int(enroll['maxValue']), 'complete': int(complete['maxValue'])} if enroll and complete else {'enroll': 0, 'complete': '0'}

  def _get_usdm(self):
    fullpath, filename = self._files.path('usdm')
    data = open(fullpath)
    return json.load(data)

  def _get_extra(self):
    fullpath, filename = self._files.path('extra')
    data = open(fullpath)
    return yaml.load(data, Loader=yaml.FullLoader)
  
