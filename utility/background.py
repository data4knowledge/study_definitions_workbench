import json
from d4kms_generic import application_logger
from usdm_db import USDMDb
from usdm_db import USDMDb, Wrapper
from model.files import Files
from model.file_import import FileImport
from model.study import Study
from model.m11_protocol.m11_protocol import M11Protocol
from model import VERSION, SYSTEM_NAME

def process_excel(uuid, user, session):
  try:
    files = Files(uuid)
    full_path = files.path(uuid, 'xlsx')
    file_import = FileImport.create(full_path, 'Processing', 'XLSX', user.id, session)
    db = USDMDb()
    file_import.update_status('Saving', session)
    errors = db.from_excel(full_path)
    files.save(uuid, 'errors', errors)
    usdm_json = db.to_json()
    files.save(uuid, 'usdm', usdm_json)
    parameters = _study_parameters(usdm_json)
    print(f"PARAMETERS: {parameters}")
    Study.study_and_version(parameters['name'], user.id, file_import.id, session)
    file_import.update_status('Successful', session)
  except Exception as e:
    if file_import:
      file_import.update_status('Exception', session)
    application_logger.exception(f"Exception '{e}' raised processing Excel file", e)

def process_word(uuid, user, session):
  try:
    files = Files(uuid)
    full_path = files.path(uuid, 'docx')
    file_import = FileImport.create(full_path, 'Processing', 'DOCX', user.id, session)
    m11 = M11Protocol(files.path(uuid, 'docx'), SYSTEM_NAME, VERSION)
    file_import.update_status('Saving', session)
    usdm_json = m11.to_usdm()
    files.save(uuid, 'usdm', usdm_json)
    parameters = _study_parameters(usdm_json)
    print(f"PARAMETERS: {parameters}")
    Study.study_and_version(parameters['name'], user.id, file_import.id, session)
    file_import.update_status('Successful', session)
  except Exception as e:
    if file_import:
      file_import.update_status('Exception', session)
    application_logger.exception(f"Exception '{e}' raised processing Word file", e)

from model.object_path import ObjectPath

def _study_parameters(json_str: str) -> dict:
  try:
    data = json.loads(json_str) 
    db = USDMDb()
    db.from_json(data)
    object_path = ObjectPath(db.wrapper())
    return {
      'name': _get_parameter(object_path, 'study/name'),
      'phase': _get_parameter(object_path, 'study/versions[0]/studyPhase/standardCode/decode'),
      'full_title': _get_parameter(object_path, "study/versions[0]/titles[type/@code='C99905x2']/text"),
    }
  except Exception as e:
    application_logger.exception(f"Exception raised extracting study parameters", e)
    return None
  
def _get_parameter(object_path: ObjectPath, path: str) -> str:
  value = object_path.get(path)
  return value if value else ''
