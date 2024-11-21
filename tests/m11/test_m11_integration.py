import re
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
  filepath, filename, media = files.path('docx')
  m11 = M11Protocol(filepath, SYSTEM_NAME, VERSION)
  await m11.process()
  result = m11.to_usdm()
  x = match_uuid('"id": "8b7907cf-6f9d-482f-b6e3-6ac23fde7ed0",')
  print(f"MATCH: {x}")
  result = re.sub(r'[a-f0-9]{8}-?[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-?[a-f0-9]{12}]', 'FAKE-UUID', result)
  print(f"RESULT: {uuid} {result[0: 70]}")
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
  await _run_test('radvax')

def match_uuid(result):
  regex = re.compile(r'.*[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}.*')
  match = regex.match(result)
  return bool(match)