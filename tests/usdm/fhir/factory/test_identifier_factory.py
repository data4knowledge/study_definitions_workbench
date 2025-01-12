from app.usdm.fhir.factory.identifier_factory import IdentifierFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called


def test_identifier():
    params = {"system": "urn:ietf:rfc:3986", "value": "urn:uuid:1234-5678.91011"}
    expected = {
        "system": "urn:ietf:rfc:3986",
        "value": "urn:uuid:1234-5678.91011",
    }
    result = IdentifierFactory(**params)
    assert result.item is not None
    assert DictResult(result.item).result == expected


def test_label_type_error(mocker):
    he = mock_handle_exception(mocker)
    params = {"valueString": (1, 2)}  # Force an exception, code not a string type
    result = IdentifierFactory(**params)
    assert result.item is None
    assert mock_called(he)
