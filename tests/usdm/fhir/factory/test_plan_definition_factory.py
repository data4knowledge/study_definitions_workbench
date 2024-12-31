from app.usdm.fhir.factory.plan_definition_factory import PlanDefinitionFactory
from tests.usdm.fhir.factory.dict_result import DictResult

def test_plan_definition():
  params = {"status": "active"}
  expected = {
    'resourceType': 'PlanDefinition',
    'status': 'active',
  }
  result = PlanDefinitionFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_plan_definition_error():
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = PlanDefinitionFactory(**params)
  assert result.item is None
