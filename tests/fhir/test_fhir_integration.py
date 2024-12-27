import pytest
from tests.files. files import *
from app.usdm.fhir.from_fhir_v1 import FromFHIRV1
from app.usdm.fhir.to_fhir_v1 import ToFHIRV1
from app.usdm.fhir.to_fhir_v2 import ToFHIRV2
from app.model.file_handling.data_files import DataFiles
from usdm_db import USDMDb

WRITE_FILE = False

@pytest.fixture
def anyio_backend():
  return 'asyncio'

async def _run_test_from_v1(name, save=False):
  version = 'v1'
  mode = 'from'
  filename = f"{name}_fhir.json"
  contents = read_json(_full_path(filename, version, mode))
  files = DataFiles()
  uuid = files.new()
  files.save("fhir", contents, filename)
  fhir = FromFHIRV1(uuid)
  result = await fhir.to_usdm()
  result = result.replace(uuid, 'FAKE-UUID') # UUID allocated is dynamic, make fixed
  pretty_result = json.dumps(json.loads(result), indent=2)
  result_filename = f"{name}_usdm.json"
  if save:
    write_json(_full_path(result_filename, version, mode), result)
  expected = read_json(_full_path(result_filename, version, mode))
  assert pretty_result == expected

async def _run_test_to_v1(name, save=False):
  version = 'v1'
  mode = 'to'
  filename = f"{name}_usdm.json"
  contents = json.loads(read_json(_full_path(filename, version, mode)))
  usdm = USDMDb()
  usdm.from_json(contents)
  study = usdm.wrapper().study
  extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
  result = ToFHIRV1(study, 'FAKE-UUID', extra).to_fhir()

  x = re.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}[+-]\d\d:\d\d$', result)
  print("Dates found:", x.groupdict())

  pretty_result = json.dumps(json.loads(result), indent=2)
  result_filename = f"{name}_fhir.json"
  if save:
    write_json(_full_path(result_filename, version, mode), result)
  expected = read_json(_full_path(result_filename, version, mode))
  assert pretty_result == expected

def _full_path(filename, version, mode):
  return f"tests/test_files/fhir_{version}/{mode}/{filename}"

@pytest.mark.anyio
async def test_from_fhir_v1_ASP8062():
  await _run_test_from_v1('ASP8062', WRITE_FILE)

@pytest.mark.anyio
async def test_from_fhir_v1_DEUCRALIP():
  await _run_test_from_v1('DEUCRALIP', WRITE_FILE)

@pytest.mark.anyio
async def test_from_fhir_v1_IGBJ():
  await _run_test_from_v1('IGBJ', WRITE_FILE)

@pytest.mark.anyio
async def test_to_fhir_v1_pilot():
  await _run_test_to_v1('pilot', WRITE_FILE)

@pytest.mark.anyio
async def test_to_fhir_v1_ASP8062():
  await _run_test_to_v1('ASP8062', True)
