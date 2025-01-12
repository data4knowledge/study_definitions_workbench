from app.usdm.fhir.factory.plan_definition_related_action_factory import (
    PlanDefinitionRelatedActionFactory,
)
from tests.usdm.fhir.factory.dict_result import DictResult
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called


def test_plan_definition_action():
    params = {"relationship": "before", "targetId": "aaaa"}
    expected = {"relationship": "before", "targetId": "aaaa"}
    result = PlanDefinitionRelatedActionFactory(**params)
    assert result.item is not None
    assert DictResult(result.item).result == expected


def test_plan_definition_action_error(mocker):
    he = mock_handle_exception(mocker)
    params = {"valueString": (1, 2)}  # Force an exception, code not a string type
    result = PlanDefinitionRelatedActionFactory(**params)
    assert result.item is None
    assert mock_called(he)
