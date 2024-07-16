from d4kms_generic import application_logger
from usdm_db import USDMDb
from model.files import Files
from model.file_import import FileImport
from model.m11_protocol.m11_protocol import M11Protocol
from model import VERSION, SYSTEM_NAME

def process_excel(uuid, user, session):
  try:
    files = Files(uuid)
    full_path = files.path(uuid, 'xlsx')
    file_import = FileImport.create(full_path, '', 'Processing', user.id, session)
    db = USDMDb()
    file_import.update_status('Saving', session)
    errors = db.from_excel(full_path)
    files.save(uuid, 'errors', errors)
    files.save(uuid, 'usdm', db.to_json())
    file_import.update_status('Successful', session)
  except Exception as e:
    file_import.update_status('Exception')
    application_logger.exception(f"Exception '{e}' raised processing Excel file", e)

def process_word(uuid, user, session):
  try:
    files = Files(uuid)
    full_path = files.path(uuid, 'docx')
    file_import = FileImport.create(full_path, '', 'Processing', user.id, session)
    m11 = M11Protocol(files.path(uuid, 'docx'), SYSTEM_NAME, VERSION)
    file_import.update_status('Saving', session)
    files.save(uuid, 'usdm', m11.to_usdm())
    file_import.update_status('Successful', session)
  except Exception as e:
    file_import.update_status('Exception')
    application_logger.exception(f"Exception '{e}' raised processing Word file", e)
