from d4kms_generic import application_logger
from usdm_db import USDMDb
from model.files import Files
from model.m11_protocol.m11_protocol import M11Protocol

def process_excel(uuid):
  try:
    files = Files(uuid)
    db = USDMDb()
    errors = db.from_excel(files.path(uuid, 'xlsx'))
    files.save(uuid, 'errors', errors)
    files.save(uuid, 'usdm', db.to_json())
  except Exception as e:
    application_logger.exception(f"Exception '{e}' raised processing Excel file", e)

def process_word(uuid):
  try:
    files = Files(uuid)
    m11 = M11Protocol(files.path(uuid, 'docx'))
    files.save(uuid, 'usdm', m11.to_usdm())
  except Exception as e:
    application_logger.exception(f"Exception '{e}' raised processing Excel file", e)
