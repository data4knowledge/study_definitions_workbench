from tests.files. files import *
from usdm_db import USDMDb
from app.model.file_handling.data_files import DataFiles

def _run_test(name, save=False):
  filename = f"{name}.xlsx"
  contents = read_excel(_full_path(filename))
  files = DataFiles()
  uuid = files.new()
  files.save("xlsx", contents, filename)
  db = USDMDb()
  errors = db.from_excel(_full_path(filename))
  result = db.to_json()
  result = result.replace(uuid, 'FAKE-UUID') # UUID allocated is dynamic, make fixed
  pretty_result = json.dumps(json.loads(result), indent=2)
  result_filename = filename = f"{name}-usdm.json"
  if save:
    write_json(_full_path(result_filename), result)
  expected = read_json(_full_path(result_filename))
  assert pretty_result == expected

def _full_path(filename):
  return f"tests/test_files/excel/{filename}"

def test_excel_pilot():
  _run_test('pilot', True)
