from app.usdm.fhir.factory.research_study_factory import ResearchStudyFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm_db import USDMDb
from tests.files. files import *

SAVE = False

def test_label_type():
  contents = json.loads(read_json(_full_path('pilot_usdm.json')))
  extra = read_yaml(_full_path(f"pilot_extra.yaml"))
  usdm = USDMDb()
  usdm.from_json(contents)
  study = usdm.wrapper().study
  result = ResearchStudyFactory(study, extra)
  assert result.item is not None
  result_dict = DictResult(result.item).result
  pretty_result = json.dumps(result_dict, indent=2)
  result_filename = f"pilot_fhir_soa.json"
  if SAVE:
    write_json(_full_path(result_filename), json.dumps(result_dict, indent=2))
  expected = read_json(_full_path(result_filename))
  assert pretty_result == expected

def test_label_type_error():
  result = ResearchStudyFactory(None)
  assert result.item is None

def _full_path(filename):
  return f"tests/test_files/fhir_v2/to/{filename}"