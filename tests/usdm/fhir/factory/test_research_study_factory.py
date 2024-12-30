from app.usdm.fhir.factory.research_study_factory import ResearchStudyFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from usdm_db import USDMDb
from tests.files. files import *

def test_label_type():
  contents = json.loads(read_json(_full_path('pilot_usdm.json')))
  extra = read_yaml(_full_path(f"pilot_extra.yaml"))
  usdm = USDMDb()
  usdm.from_json(contents)
  study = usdm.wrapper().study
  result = ResearchStudyFactory(study, extra)
  assert result.item is not None
  assert DictResult(result.item).result == {}

def test_label_type_error():
  result = ResearchStudyFactory(None)
  assert result.item is None

def _full_path(filename):
  return f"tests/test_files/fhir_v2/to/{filename}"