#from fastapi import Depends, FastAPI, Request, BackgroundTasks
from d4kms_generic import application_logger
from usdm_info import __package_version__ as code_version
from usdm_info import __model_version__ as model_version
from usdm_db import USDMDb

def process_excel(uuid):
  try:
    files = Files(manifest_lock)
    acquired = excel_lock.acquire(timeout=EXCEL_TIMEOUT)
    if acquired:
      db = USDMDb()
      errors = db.from_excel(files.source_file(uuid))
      fhir_json = db.to_fhir() if db.was_m11() else None
      files.save(uuid, db.to_json(), errors, fhir_json, db.to_timeline(USDMDb.BODY_HTML), db.to_pdf(), db.to_html(), db.to_html(True))
      excel_lock.release()
    else:
      files.timeout(uuid)
      application_logger.error(f"Excel lock timeout for '{uuid}")
  except Exception as e:
    application_logger.exception(f"Exception '{e}' raised processing Excel file", e)
