import pytest
from tests.files.files import *
from tests.helpers.helpers import fix_uuid, fix_iso_dates
from app.usdm.fhir.from_fhir_v1 import FromFHIRV1
from app.usdm.fhir.to_fhir_v1 import ToFHIRV1
from app.usdm.fhir.to_fhir_v2 import ToFHIRV2
from app.model.file_handling.data_files import DataFiles
from usdm4 import USDM4

SAVE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _run_test_from_v1(name, save=False):
    version = "v1"
    mode = "from"
    filename = f"{name}_fhir_m11.json"
    contents = read_json(_full_path(filename, version, mode))
    files = DataFiles()
    uuid = files.new()
    files.save("fhir", contents, filename)
    fhir = FromFHIRV1(uuid)
    result = await fhir.to_usdm()
    result = result.replace(uuid, "FAKE-UUID")  # UUID allocated is dynamic, make fixed
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_usdm.json"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected


async def _run_test_to_v1(name, save=False):
    version = "v1"
    mode = "to"
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(_full_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
    result = ToFHIRV1(study, "FAKE-UUID", extra).to_fhir()
    result = fix_iso_dates(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_m11.json"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected


async def _run_test_to_v2(name, save=False):
    version = "v2"
    mode = "to"
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(_full_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
    result = ToFHIRV2(study, "FAKE-UUID", extra).to_fhir()
    result = fix_iso_dates(result)
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_m11.json"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected


def _full_path(filename, version, mode):
    return f"tests/test_files/fhir_{version}/{mode}/{filename}"


@pytest.mark.anyio
async def test_from_fhir_v1_ASP8062():
    await _run_test_from_v1("ASP8062", SAVE)


@pytest.mark.anyio
async def test_from_fhir_v1_DEUCRALIP():
    await _run_test_from_v1("DEUCRALIP", SAVE)


@pytest.mark.anyio
async def test_from_fhir_v1_IGBJ():
    await _run_test_from_v1("IGBJ", SAVE)


@pytest.mark.anyio
async def test_to_fhir_v1_pilot():
    await _run_test_to_v1("pilot", SAVE)


@pytest.mark.anyio
async def test_to_fhir_v1_ASP8062():
    await _run_test_to_v1("ASP8062", SAVE)


@pytest.mark.anyio
async def test_to_fhir_v2_pilot():
    await _run_test_to_v2("pilot", SAVE)


@pytest.mark.anyio
async def test_to_fhir_v2_ASP8062():
    await _run_test_to_v2("ASP8062", SAVE)
