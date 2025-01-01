import re
import pytest
from tests.files.files import *
from tests.helpers.helpers import fix_uuid
from app.usdm.fhir.soa.to_fhir_soa import ToFHIRSoA
from usdm_db import USDMDb

WRITE_FILE = True

@pytest.fixture
def anyio_backend():
  return 'asyncio'

async def _run_test_to(name, save=False):
  version = 'v2'
  mode = 'to'
  filename = f"{name}_usdm.json"
  contents = json.loads(read_json(_full_path(filename, version, mode)))
  usdm = USDMDb()
  usdm.from_json(contents)
  study = usdm.wrapper().study
  extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
  result = ToFHIRSoA(study, extra).to_message()
  print(f"RESULT: {result}")
  #result = _fix_iso_dates(result)  
  pretty_result = json.dumps(json.loads(result), indent=2)
  result_filename = f"{name}_fhir_soa.json"
  if save:
    write_json(_full_path(result_filename, version, mode), result)
  expected = read_json(_full_path(result_filename, version, mode))
  assert pretty_result == expected

def _full_path(filename, version, mode):
  return f"tests/test_files/fhir_{version}/{mode}/{filename}"

# def _fix_iso_dates(text):
#   dates = re.findall(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}[+-]\d\d:\d\d', text)
#   for date in dates:
#     text = text.replace(date, '2024-12-25:00:00:00.000000+00:00')  
#   dates = re.findall(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z', text)
#   for date in dates:
#     text = text.replace(date, '2024-12-25:00:00:00.000000+00:00')  
#   return text

@pytest.mark.anyio
async def test_from_fhir_v1_ASP8062():
  await _run_test_to('pilot', WRITE_FILE)
