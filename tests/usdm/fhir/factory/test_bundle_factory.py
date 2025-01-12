from datetime import datetime, date
from zoneinfo import ZoneInfo
from app.usdm.fhir.factory.bundle_factory import BundleFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from fhir.resources.identifier import Identifier
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called


def test_bundle():
    date_obj = datetime(2024, 12, 31, 0, 0, tzinfo=ZoneInfo(key="Europe/Amsterdam"))
    date_str = date_obj.isoformat()
    identifier = Identifier(system="urn:ietf:rfc:3986", value=f"urn:uuid:1234-5678")
    params = {
        "entry": [],
        "type": "document",
        "identifier": identifier,
        "timestamp": date_str,
    }
    expected = {
        "identifier": {
            "system": "urn:ietf:rfc:3986",
            "value": "urn:uuid:1234-5678",
        },
        "resourceType": "Bundle",
        "timestamp": "2024-12-31T00:00:00+01:00",
        "type": "document",
    }
    result = BundleFactory(**params)
    assert result.item is not None
    assert DictResult(result.item).result == expected


def test_bundle_error(mocker):
    he = mock_handle_exception(mocker)
    params = {"valueString": (1, 2)}  # Force an exception, code not a string type
    result = BundleFactory(**params)
    assert result.item is None
    assert mock_called(he)
