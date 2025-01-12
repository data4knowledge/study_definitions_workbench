from app.usdm.fhir.factory.research_study_factory import ResearchStudyFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm_db import USDMDb
from tests.files.files import *
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

PATH = f"tests/test_files/fhir_v2/to/"
SAVE = False


def test_research_study():
    contents = json.loads(read_json(_full_path("pilot_usdm.json")))
    extra = read_yaml(_full_path(f"pilot_extra.yaml"))
    usdm = USDMDb()
    usdm.from_json(contents)
    study = usdm.wrapper().study
    result = ResearchStudyFactory(study, extra)
    assert result.item is not None
    result_dict = DictResult(result.item)
    assert result_dict.results_match_file(PATH, f"pilot_fhir_soa_rs.json", SAVE)


def test_research_study_error(mocker):
    he = mock_handle_exception(mocker)
    result = ResearchStudyFactory(None)
    assert result.item is None
    assert mock_called(he)


def _full_path(filename):
    return f"tests/test_files/fhir_v2/to/{filename}"
