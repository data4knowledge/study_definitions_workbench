import pytest
from tests.files. files import *
from app.USDM.fhir.from_fhir_v1 import FromFHIRV1
from app.model.file_handling.data_files import DataFiles

WRITE_FILE = False

@pytest.fixture
def anyio_backend():
  return 'asyncio'

async def _run_test(name, save=False):
  filename = f"{name}.json"
  contents = read_json(_full_path(filename))
  files = DataFiles()
  uuid = files.new()
  files.save("fhir", contents, filename)
  fhir = FromFHIRV1(uuid)
  result = await fhir.to_usdm()
  result = result.replace(uuid, 'FAKE-UUID') # UUID allocated is dynamic, make fixed
  pretty_result = json.dumps(json.loads(result), indent=2)
  result_filename = filename = f"{name}-usdm.json"
  if save:
    write_json(_full_path(result_filename), result)
  expected = read_json(_full_path(result_filename))
  assert pretty_result == expected

def _full_path(filename):
  return f"tests/test_files/fhir_v1/{filename}"

@pytest.mark.anyio
async def test_fhir_v1_ASP8062():
  await _run_test('ASP8062', WRITE_FILE)

@pytest.mark.anyio
async def test_fhir_v1_DEUCRALIP():
  await _run_test('DEUCRALIP', WRITE_FILE)

@pytest.mark.anyio
async def test_fhir_v1_IGBJ():
  await _run_test('IGBJ', WRITE_FILE)
