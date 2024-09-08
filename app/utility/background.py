import json
from d4kms_generic import application_logger
from usdm_db import USDMDb
from usdm_db import USDMDb, Wrapper
from app.model.files import Files
from app.model.file_import import FileImport
from app.model.study import Study
from app.model.user import User
from app.model.m11_protocol.m11_protocol import M11Protocol
from app.model.fhir.from_fhir_v1 import FromFHIRV1
from app import VERSION, SYSTEM_NAME
from sqlalchemy.orm import Session
from app.model.object_path import ObjectPath

def process_excel(uuid, user: User, session: Session) -> None:
  try:
    file_import = None
    files = Files(uuid)
    full_path, filename = files.path('xlsx')
    file_import = FileImport.create(full_path, filename, 'Processing', 'XLSX', uuid, user.id, session)
    db = USDMDb()
    file_import.update_status('Saving', session)
    errors = db.from_excel(full_path)
    files.save('errors', errors)
    usdm_json = db.to_json()
    files.save('usdm', usdm_json)
    parameters = _study_parameters(usdm_json)
    #print(f"PARAMETERS: {parameters}")
    Study.study_and_version(parameters, user, file_import, session)
    file_import.update_status('Successful', session)
  except Exception as e:
    if file_import:
      file_import.update_status('Exception', session)
    application_logger.exception(f"Exception '{e}' raised processing Excel file", e)

def process_word(uuid, user: User, session: Session) -> None:
  try:
    file_import = None
    files = Files(uuid)
    full_path, filename = files.path('docx')
    file_import = FileImport.create(full_path, filename, 'Processing', 'DOCX', uuid, user.id, session)
    m11 = M11Protocol(full_path, SYSTEM_NAME, VERSION)
    file_import.update_status('Saving', session)
    usdm_json = m11.to_usdm()
    files.save('usdm', usdm_json)
    files.save('extra', {'extensions': m11.extra()})
    parameters = _study_parameters(usdm_json)
    #print(f"PARAMETERS: {parameters}")
    Study.study_and_version(parameters, user, file_import, session)
    file_import.update_status('Successful', session)
  except Exception as e:
    if file_import:
      file_import.update_status('Exception', session)
    application_logger.exception(f"Exception '{e}' raised processing Word file", e)

def process_fhir_v1(uuid, user: User, session: Session) -> None:
  try:
    file_import = None
    files = Files(uuid)
    full_path, filename = files.path('fhir')
    file_import = FileImport.create(full_path, filename, 'Processing', 'FHIR V1', uuid, user.id, session)
    file_import.update_status('Saving', session)
    fhir = FromFHIRV1(uuid)
    file_import.update_status('Saving', session)
    usdm_json = fhir.to_usdm()
    files.save('usdm', usdm_json)
    parameters = _study_parameters(usdm_json)
    print(f"PARAMETERS: {parameters}")
    Study.study_and_version(parameters, user, file_import, session)
    file_import.update_status('Successful', session)
  except Exception as e:
    if file_import:
      file_import.update_status('Exception', session)
    application_logger.exception(f"Exception '{e}' raised processing FHIR V1 file", e)

def _study_parameters(json_str: str) -> dict:
  try:
    data = json.loads(json_str) 
    db = USDMDb()
    db.from_json(data)
    object_path = ObjectPath(db.wrapper())
    return {
      'name': _get_parameter(object_path, 'study/name'),
      'phase': _get_parameter(object_path, 'study/versions[0]/studyPhase/standardCode/decode'),
      #'full_title': _get_parameter(object_path, "study/versions[0]/titles[type/@code='C99905x2']/text"),
      'full_title': _official_title(db.wrapper()),
      'sponsor_identifier': _sponsor_identifier(db.wrapper()),
      'nct_identifier': _nct_identifier(db.wrapper()),
      'sponsor': _sponsor(db.wrapper()),
    }
  except Exception as e:
    application_logger.exception(f"Exception raised extracting study parameters", e)
    return None
  
def _get_parameter(object_path: ObjectPath, path: str) -> str:
  value = object_path.get(path)
  return value if value else ''

# Temporary
def _official_title(wrapper: Wrapper):
  study_version = wrapper.study.versions[0]
  title_type = 'Official Study Title'
  for title in study_version.titles:
    if title.type.decode == title_type:
      return title.text
  return ''

def _sponsor_identifier(wrapper: Wrapper):
  study_version = wrapper.study.versions[0]
  identifiers = study_version.studyIdentifiers
  for identifier in identifiers:
    if identifier.studyIdentifierScope.organizationType.code == 'C70793':
      return identifier.studyIdentifier
  return ''

def _nct_identifier(wrapper: Wrapper):
  study_version = wrapper.study.versions[0]
  identifiers = study_version.studyIdentifiers
  for identifier in identifiers:
    if identifier.studyIdentifierScope.name == 'ClinicalTrials.gov':
      return identifier.studyIdentifier
  return ''

def _sponsor(wrapper: Wrapper):
  study_version = wrapper.study.versions[0]
  identifiers = study_version.studyIdentifiers
  for identifier in identifiers:
    if identifier.studyIdentifierScope.organizationType.code == 'C70793':
      return identifier.studyIdentifierScope.name
  return ''
