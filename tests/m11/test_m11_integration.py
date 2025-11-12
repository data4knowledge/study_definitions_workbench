import re
import json
import pytest
from tests.files.files import write_json, read_json, read_word
from app.model.file_handling.data_files import DataFiles
from usdm4_m11 import USDM4M11
from usdm4.api.wrapper import Wrapper

SAVE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _run_test(dir, name, save=False):
    filename = f"{name}.docx"
    contents = read_word(_full_path(dir, filename))
    files = DataFiles()
    _ = files.new()
    files.save("docx", contents, filename)
    filepath, filename, media = files.path("docx")
    m11 = USDM4M11()
    wrapper: Wrapper = m11.from_docx(filepath)
    result = wrapper.to_json()
    result = replace_uuid(result)
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
    await _run_test("RadVax", "RadVax", SAVE)


@pytest.mark.anyio
async def test_m11_wa42380():
    await _run_test("WA42380", "WA42380", SAVE)


@pytest.mark.anyio
async def test_m11_lzzt():
    await _run_test("LZZT", "LZZT", SAVE)


@pytest.mark.anyio
async def test_m11_asp8062():
    await _run_test("ASP8062", "ASP8062", SAVE)


def replace_uuid(result):
    return re.sub(
        r"[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}",
        "FAKE",
        result,
    )
