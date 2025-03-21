import re
import pytest
from tests.files.files import *
from app.model.file_handling.data_files import DataFiles
from app.model.m11_protocol.m11_protocol import M11Protocol
from app import VERSION, SYSTEM_NAME

WRITE_FILE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _run_test(dir, name, save=False):
    filename = f"{name}.docx"
    contents = read_word(_full_path(dir, filename))
    files = DataFiles()
    uuid = files.new()
    files.save("docx", contents, filename)
    filepath, filename, media = files.path("docx")
    m11 = M11Protocol(filepath, SYSTEM_NAME, VERSION)
    await m11.process()
    result = m11.to_usdm()
    result = replace_uuid(result)
    # print(f"MATCH: {result[10:70]}")
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = filename = f"{name}_usdm.json"
    if save:
        write_json(_full_path(dir, result_filename), result)
    expected = read_json(_full_path(dir, result_filename))
    assert pretty_result == expected


def _full_path(dir, filename):
    return f"tests/test_files/m11/{dir}/{filename}"


@pytest.mark.anyio
async def test_m11_radvax():
    await _run_test("RadVax", "RadVax", WRITE_FILE)


@pytest.mark.anyio
async def test_m11_wa42380():
    await _run_test("WA42380", "WA42380", WRITE_FILE)


@pytest.mark.anyio
async def test_m11_lzzt():
    await _run_test("LZZT", "LZZT", WRITE_FILE)


@pytest.mark.anyio
async def test_m11_asp8062():
    await _run_test("ASP8062", "ASP8062", WRITE_FILE)


def replace_uuid(result):
    return re.sub(
        r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
        "FAKE",
        result,
    )
