import os
import json
from app.usdm.fhir.factory.timepoint_plan_definition_factory import (
    TimepointPlanDefinitionFactory,
)
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm4 import USDM4
from usdm4.api.wrapper import Wrapper
from usdm4.api.study import Study
from usdm4.api.study_design import StudyDesign
from usdm4.api.schedule_timeline import ScheduleTimeline
from tests.files.files import read_json
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

PATH = "tests/test_files/fhir_v2/to/"
SAVE = False


def test_timeline_plan_definition():
    study = _setup()
    sd = _study_design(study)
    tl = _main_timeline(sd)
    tp = tl.instances[0]
    result = TimepointPlanDefinitionFactory(study, sd, tp)
    assert result.item is not None
    result_dict = DictResult(result.item)
    result_dict.read_expected(PATH, "pilot_fhir_soa_tppd.json", SAVE)
    assert result_dict.actual == result_dict.expected


def test_timeline_plan_definition_error(mocker):
    he = mock_handle_exception(mocker)
    result = TimepointPlanDefinitionFactory(None, None, None)
    assert result.item is None
    assert mock_called(he)


def _study_design(study: Study) -> StudyDesign:
    return study.versions[0].studyDesigns[0]


def _main_timeline(study_design: StudyDesign) -> ScheduleTimeline:
    return study_design.main_timeline()


def _setup():
    contents = json.loads(read_json(os.path.join(PATH, "pilot_usdm.json")))
    usdm = USDM4()
    wrapper: Wrapper = usdm.from_json(contents)
    return wrapper.study
