import pytest
from tests.files. files import *
from app.model.file_handling.data_files import DataFiles
from app.model.m11_protocol.m11_protocol import M11Protocol
from app import VERSION, SYSTEM_NAME

@pytest.fixture
def anyio_backend():
  return 'asyncio'

async def _run_test(name, save=False):
  filename = f"{name}.docx"
  contents = read_word(_full_path(filename))
  files = DataFiles()
  uuid = files.new()
  files.save("docx", contents, filename)
  m11 = M11Protocol(_full_path(filename), SYSTEM_NAME, VERSION)
  await m11.process()
  result = m11.to_usdm()
  result = result.replace(uuid, 'FAKE-UUID') # UUID allocated is dynamic, make fixed
  pretty_result = json.dumps(json.loads(result), indent=2)
  result_filename = filename = f"{name}-usdm.json"
  if save:
    write_json(_full_path(result_filename), result)
  expected = read_json(_full_path(result_filename))
  assert pretty_result == expected

def _full_path(filename):
  return f"tests/test_files/m11/{filename}"

@pytest.mark.anyio
async def test_excel_radvax():
  await _run_test('radvax', True)
