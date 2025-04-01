import os
import json
from app.usdm.fhir.factory.timeline_plan_definition_factory import (
    TimelinePlanDefinitionFactory,
)
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper
from usdm4.api.study import Study
from usdm4.api.schedule_timeline import ScheduleTimeline
from tests.files.files import read_json
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

PATH = "tests/test_files/fhir_v2/to/"
SAVE = False


def test_timeline_plan_definition():
    study = _setup()
    result = TimelinePlanDefinitionFactory(study, _main_timeline(study))
    assert result.item is not None
    result_dict = DictResult(result.item)
    result_dict.read_expected(PATH, "pilot_fhir_soa_tlpd.json", SAVE)
    assert result_dict.actual == result_dict.expected


def test_timeline_plan_definition_error(mocker):
    he = mock_handle_exception(mocker)
    result = TimelinePlanDefinitionFactory(None, None)
    assert result.item is None
    assert mock_called(he)


def _main_timeline(study: Study) -> ScheduleTimeline:
    timeline = study.versions[0].studyDesigns[0].main_timeline()
    return timeline


def _setup():
    contents = json.loads(read_json(os.path.join(PATH, "pilot_usdm.json")))
    usdm = USDM4()
    wrapper: Wrapper = usdm.from_json(contents)
    return wrapper.study
