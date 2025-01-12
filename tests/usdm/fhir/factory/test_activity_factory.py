import pytest
from app.usdm.fhir.factory.activity_factory import ActivityDefinitionFactory
from fhir.resources.activitydefinition import ActivityDefinition
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called


def test_activity_definition():
    # Arrange
    valid_data = {
        "status": "active",
        "name": "test-activity",
        "title": "Test Activity",
    }

    # Act
    factory = ActivityDefinitionFactory(**valid_data)

    # Assert
    assert factory.item is not None
    assert isinstance(factory.item, ActivityDefinition)
    assert factory.item.status == "active"
    assert factory.item.name == "test-activity"
    assert factory.item.title == "Test Activity"


def test_activity_definition_error(mocker):
    he = mock_handle_exception(mocker)
    params = {"valueString": (1, 2)}  # Force an exception, code not a string type
    result = ActivityDefinitionFactory(**params)
    assert result.item is None
    assert mock_called(he)
