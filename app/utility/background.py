import json
import threading
import asyncio
from app.model.database import SessionLocal
from d4kms_generic import application_logger
from usdm_db import USDMDb
from usdm_db import USDMDb, Wrapper
from app.model.files import Files
from app.model.file_import import FileImport
from app.model.study import Study
from app.model.user import User
from app.model.m11_protocol.m11_protocol import M11Protocol
from app.model.fhir.from_fhir_v1 import FromFHIRV1
from app.model.connection_manager import connection_manager
from app import VERSION, SYSTEM_NAME
from sqlalchemy.orm import Session
from app.model.object_path import ObjectPath

async def process_excel(uuid, user: User) -> None:
  try:
    session = SessionLocal()
    # print("Background running")
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
    files.save('extra', _blank_extra())
    parameters = _study_parameters(usdm_json)
    # print(f"PARAMETERS: {parameters}")
    Study.study_and_version(parameters, user, file_import, session)
    file_import.update_status('Successful', session)
    session.close()
    await connection_manager.success(f"Import of Excel workbook completed sucessfully", str(user.id))
  except Exception as e:
    if file_import:
      file_import.update_status('Exception', session)
    application_logger.exception(f"Exception '{e}' raised processing Excel file", e)
    session.close()
    await connection_manager.error(f"Error encountered importing Excel workbook", str(user.id))

async def process_word(uuid, user: User) -> None:
  try:
    session = SessionLocal()
    file_import = None
    files = Files(uuid)
    full_path, filename = files.path('docx')
    file_import = FileImport.create(full_path, filename, 'Processing', 'DOCX', uuid, user.id, session)
    m11 = M11Protocol(full_path, SYSTEM_NAME, VERSION)
    await m11.process()
    file_import.update_status('Saving', session)
    usdm_json = m11.to_usdm()
    files.save('usdm', usdm_json)
    files.save('extra', m11.extra())
    parameters = _study_parameters(usdm_json)
    Study.study_and_version(parameters, user, file_import, session)
    file_import.update_status('Successful', session)
    session.close()
    await connection_manager.success(f"Import of M11 document completed sucessfully", str(user.id))
  except Exception as e:
    if file_import:
      file_import.update_status('Exception', session)
    application_logger.exception(f"Exception '{e}' raised processing Word file", e)
    session.close()
    await connection_manager.error(f"Error encountered importing M11 document", str(user.id))

async def process_fhir_v1(uuid, user: User) -> None:
  try:
    session = SessionLocal()
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
    # print(f"PARAMETERS: {parameters}")
    Study.study_and_version(parameters, user, file_import, session)
    file_import.update_status('Successful', session)
    session.close()
    await connection_manager.success(f"Import of FHIR message completed succesfully", str(user.id))
  except Exception as e:
    if file_import:
      file_import.update_status('Exception', session)
    application_logger.exception(f"Exception '{e}' raised processing FHIR V1 file", e)
    session.close()
    await connection_manager.error(f"Error encountered importing FHIR message", str(user.id))

def run_background_task(name, uuid, user: User) -> None:
  t = threading.Thread(target=asyncio.run, args=(name(uuid, user),))
  t.start()

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

def _blank_extra():
  return {
    'amendment': {
      'amendment_details': '',
      'robustness_impact': False,
      'robustness_impact_reason': '',
      'safety_impact': False,
      'safety_impact_reason': ''
    },
    'miscellaneous': {
      'medical_expert_contact': '',
      'sae_reporting_method': '',
      'sponsor_signatory': ''
    },
    'title_page': {
      'amendment_details': '',
      'amendment_identifier': '',
      'amendment_scope': '',
      'compound_codes': '',
      'compound_names': '',
      'manufacturer_name_and_address': '',
      'medical_expert_contact': '',
      'original_protocol': '',
      'regulatory_agency_identifiers': '',
      'sae_reporting_method': '',
      'sponsor_approval_date': '',
      'sponsor_confidentiality': '',
      'sponsor_name_and_address': '',
      'sponsor_signatory': ''
    }
  }
