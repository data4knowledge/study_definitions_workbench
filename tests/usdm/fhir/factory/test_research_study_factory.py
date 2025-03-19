import json
from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper
from app.usdm.fhir.factory.research_study_factory import ResearchStudyFactory
from tests.usdm.fhir.factory.dict_result import DictResult

# from usdm_db import USDMDb
from tests.files.files import read_json, read_yaml
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

PATH = "tests/test_files/fhir_v2/to/"
SAVE = False


def test_research_study():
    contents = json.loads(read_json(_full_path("pilot_usdm.json")))
    extra = read_yaml(_full_path("pilot_extra.yaml"))
    usdm = USDM4()
    wrapper: Wrapper = usdm.from_json(contents)
    study = wrapper.study
    result = ResearchStudyFactory(study, extra)
    assert result.item is not None
    result_dict = DictResult(result.item)
    result_dict.read_expected(PATH, "pilot_fhir_soa_rs.json", SAVE)
    assert result_dict.actual == result_dict.expected


def test_research_study_error(mocker):
    he = mock_handle_exception(mocker)
    result = ResearchStudyFactory(None)
    assert result.item is None
    assert mock_called(he)


def _full_path(filename):
    return f"{PATH}/{filename}"
