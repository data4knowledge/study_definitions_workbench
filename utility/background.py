from d4kms_generic import application_logger
from usdm_db import USDMDb
from model.files import Files

def process_excel(uuid):
  try:
    files = Files()
    db = USDMDb()
    errors = db.from_excel(files.read(uuid, 'xlsx'))
    files.save(uuid, 'errors', errors)
    files.save(uuid, 'usdm', db.to_json())
  except Exception as e:
    application_logger.exception(f"Exception '{e}' raised processing Excel file", e)
