import json
import warnings
from model.file_import import FileImport
from model.files import Files
from model.version import Version
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

class USDMJson():

  def __init__(self, id: int, session: Session):
    self.id = id
    version = Version.find(id, session)
    file_import = FileImport.find(version.import_id, session)
    self.uuid = file_import.uuid
    self.type = file_import.type
    self.m11 = True if self.type == "DOCX" else False
    files = Files(file_import.uuid)
    fullpath, filename = files.path('usdm')
    data = open(fullpath)
    self._data = json.load(data)

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
    design = self._study_design(id)
    if design:
      result = {
        'id': self.id,
        'trial_types': {},
        'trial_intent': {},
        'intervention_model': None,
        'therapeutic_areas': {},
        'characteristics': {},
        'population':  None
      }
      for item in design['trialIntentTypes']:
        result['trial_intent'][item['decode']] = item['decode']
      for item in design['trialTypes']:
        result['trial_types'][item['decode']] = item['decode']
      result['intervention_model'] = design['interventionModel']['decode']
      for item in design['characteristics']:
        result['characteristics'][item['decode']] = item['decode']
      return result
    else:
      return None

  def study_design_design_parameters(self, id: str):
    design = self._study_design(id)
    if design:
      result = {
        'id': self.id,
        'arms': 0,
        'trial_blind_scheme': {},
        'blinded_roles': {},
        'participants': None,
        'duration': None,
        'independent_committee':  None
      }
      result['arms'] = len(design['arms'])
      return result
    else:
      return None

  def study_design_schema(self, id: str):
    design = self._study_design(id)
    if design:
      section = self._section_by_number("1.2") if self.m11 else self._section_by_title_contains("study design")
      return self._image_in_section(section)

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
