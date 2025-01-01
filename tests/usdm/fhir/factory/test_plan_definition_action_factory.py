from app.usdm.fhir.factory.plan_definition_action_factory import PlanDefinitionActionFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from fhir.resources.coding import Coding
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

def test_plan_definition_action():
  params = {'coding': [Coding(system='Code System', version='1', code='Code', display='Decode')]}
  result = CodeableConceptFactory(**params)
  params = {'code': result.item}
  expected = {     
    'code': {
      'coding': [
        {
            'code': 'Code',
            'display': 'Decode',
            'system': 'Code System',
            'version': '1',
        },
      ]
    }
  }
  result = PlanDefinitionActionFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_plan_definition_action_error(mocker):
  he = mock_handle_exception(mocker)
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = PlanDefinitionActionFactory(**params)
  assert result.item is None
  assert mock_called(he)
