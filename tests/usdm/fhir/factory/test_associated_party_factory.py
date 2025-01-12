from app.usdm.fhir.factory.associated_party_factory import AssociatedPartyFactory
from tests.usdm.fhir.factory.dict_result import DictResult
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called


def test_associated_party_display():
    params = {"role_code": "xxx", "role_display": "yyy", "party": {"display": "1234"}}
    expected = {
        "party": {
            "display": "1234",
        },
        "role": {
            "coding": [
                {
                    "code": "xxx",
                    "display": "yyy",
                    "system": "http://hl7.org/fhir/research-study-party-role",
                },
            ],
        },
    }
    result = AssociatedPartyFactory(**params)
    assert result.item is not None
    assert DictResult(result.item).result == expected


def test_associated_party_reference():
    params = {"role_code": "xxx", "role_display": "yyy", "party": {"reference": "1234"}}
    expected = {
        "party": {
            "reference": "1234",
        },
        "role": {
            "coding": [
                {
                    "code": "xxx",
                    "display": "yyy",
                    "system": "http://hl7.org/fhir/research-study-party-role",
                },
            ],
        },
    }
    result = AssociatedPartyFactory(**params)
    assert result.item is not None
    assert DictResult(result.item).result == expected


def test_associated_party_error(mocker):
    he = mock_handle_exception(mocker)
    params = {"valueString": (1, 2)}  # Force an exception, code not a string type
    result = AssociatedPartyFactory(**params)
    assert result.item is None
    assert mock_called(he)
