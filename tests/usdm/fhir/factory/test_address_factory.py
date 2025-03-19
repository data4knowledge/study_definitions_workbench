from app.usdm.fhir.factory.address_factory import AddressFactory
from usdm_model.address import Address
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called


def test_address():
    address_dict = {
        "city": "city",
        "country": {
            "code": "code",
            "codeSystem": "codesys",
            "codeSystemVersion": "3",
            "decode": "USA",
            "id": "Code1",
            "instanceType": "Code",
        },
        "district": "district",
        "id": "Addr_1",
        "instanceType": "Address",
        "lines": ["Line 1"],
        "postalCode": "postal code",
        "state": "state",
        "text": "line 1, city, district, state, postal code, USA",
    }
    expected = {
        "city": "city",
        "country": "USA",
        "district": "district",
        "id": "Addr_1",
        "lines": ["Line 1"],
        "postalCode": "postal code",
        "state": "state",
        "text": "line 1, city, district, state, postal code, USA",
    }
    address = Address(**address_dict)
    result = AddressFactory(address)
    assert result.item is not None
    assert result.item == expected


def test_address_error(mocker):
    he = mock_handle_exception(mocker)
    result = AddressFactory({})
    assert result.item is None
    assert mock_called(he)
