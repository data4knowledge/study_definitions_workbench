import os
from app.usdm.fhir.factory.timeline_plan_definition_factory import TimelinePlanDefinitionFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm_db import USDMDb
from usdm_model.study import Study
from usdm_model.schedule_timeline import ScheduleTimeline
from tests.files. files import *

PATH = f"tests/test_files/fhir_v2/to/"
SAVE = True

def test_identifier():
  study = _setup()
  result = TimelinePlanDefinitionFactory._identifier(_main_timeline(study))
  assert result.item is not None
  result_dict = DictResult(result.item)
  assert result_dict.dict == {
    'use': 'usual', 
    'type': {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/v2-0203', 'code': 'PLAC'}]}, 
    'value': 'Main Timeline'
  }

def test_timeline_plan_definition():
  study = _setup()
  result = TimelinePlanDefinitionFactory(_main_timeline(study))
  assert result.item is not None
  result_dict = DictResult(result.item)
  assert result_dict.results_match_file(PATH, f"pilot_fhir_soa_tpd.json", SAVE)

def test_timeline_plan_definition_error():
  result = TimelinePlanDefinitionFactory(None)
  assert result.item is None

def _main_timeline(study: Study) -> ScheduleTimeline:
  timeline = study.versions[0].studyDesigns[0].main_timeline()
  print(f"Timeline: {timeline.name}")
  return timeline

def _setup():
  contents = json.loads(read_json(os.path.join(PATH, 'pilot_usdm.json')))
  usdm = USDMDb()
  usdm.from_json(contents)
  return usdm.wrapper().study
