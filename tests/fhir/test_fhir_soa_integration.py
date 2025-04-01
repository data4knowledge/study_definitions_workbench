import pytest
from tests.files.files import *
from tests.helpers.helpers import fix_uuid, fix_iso_dates
from app.usdm.fhir.soa.to_fhir_soa import ToFHIRSoA
from usdm4 import USDM4
from usdm4.api.study import *
from usdm4.api.study_design import *

SAVE = False


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _run_test_to(name, save=False):
    version = "v2"
    mode = "to"
    filename = f"{name}_usdm.json"
    contents = json.loads(read_json(_full_path(filename, version, mode)))
    usdm = USDM4()
    wrapper = usdm.from_json(contents)
    study = wrapper.study
    extra = read_yaml(_full_path(f"{name}_extra.yaml", version, mode))
    study_version = study.first_version()
    study_design = study_version.studyDesigns[0]
    result = ToFHIRSoA(
        study, study_design.main_timeline().id, "FAKE-UUID", extra
    ).to_message()
    result = fix_iso_dates(result)
    result = fix_uuid(result)
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = f"{name}_fhir_soa.json"
    if save:
        write_json(_full_path(result_filename, version, mode), result)
    expected = read_json(_full_path(result_filename, version, mode))
    assert pretty_result == expected


def _full_path(filename, version, mode):
    return f"tests/test_files/fhir_{version}/{mode}/{filename}"


@pytest.mark.anyio
async def test_from_fhir_v1_ASP8062():
    await _run_test_to("pilot", SAVE)
