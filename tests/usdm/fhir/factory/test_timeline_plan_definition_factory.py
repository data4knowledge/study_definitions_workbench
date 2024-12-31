from app.usdm.fhir.factory.timeline_plan_definition_factory import TimelinePlanDefinitionFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm_db import USDMDb
from usdm_model.study import Study
from usdm_model.schedule_timeline import ScheduleTimeline
from tests.files. files import *

SAVE = True

def test_timeline_plan_definition():
  contents = json.loads(read_json(_full_path('pilot_usdm.json')))
  usdm = USDMDb()
  usdm.from_json(contents)
  study = usdm.wrapper().study
  result = TimelinePlanDefinitionFactory(_main_timeline(study))
  assert result.item is not None
  result_dict = DictResult(result.item).result
  pretty_result = json.dumps(result_dict, indent=2)
  result_filename = f"pilot_fhir_soa_tpd.json"
  if SAVE:
    write_json(_full_path(result_filename), json.dumps(result_dict, indent=2))
  expected = read_json(_full_path(result_filename))
  assert pretty_result == expected

def test_timeline_plan_definition_error():
  result = TimelinePlanDefinitionFactory(None)
  assert result.item is None

def _full_path(filename):
  return f"tests/test_files/fhir_v2/to/{filename}"

def _main_timeline(study: Study) -> ScheduleTimeline:
  timeline = study.versions[0].studyDesigns[0].main_timeline()
  print(f"Timeline: {timeline.name}")
  return timeline