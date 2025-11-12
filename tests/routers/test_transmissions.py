import pytest
from tests.mocks.general_mocks import mock_called
from tests.mocks.user_mocks import mock_user_check_exists
from tests.mocks.fastapi_mocks import protect_endpoint, mock_client
from tests.mocks.utility_mocks import (
    mock_transmit_role_enabled_true,
    mock_transmit_role_enabled_false,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_transmisison_status_authorised(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    ift = mock_transmit_role_enabled_true(mocker)
    response = client.get("/transmissions/status?page=1&size=10")
    assert response.status_code == 200
    assert """Status of the transmissions perfomed by you""" in response.text
    assert mock_called(uc)
    assert mock_called(ift)


def test_transmisison_status_not_authorised(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    ift = mock_transmit_role_enabled_false(mocker)
    response = client.get("/transmissions/status?page=1&size=10")
    assert response.status_code == 200
    assert """User is not authorised to transmit FHIR messages.""" in response.text
    assert mock_called(uc)
    assert mock_called(ift)


def test_transmisison_status_data_authorised(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    ift = mock_transmit_role_enabled_true(mocker)
    response = client.get("/transmissions/status/data?page=1&size=10")
    assert response.status_code == 200
    assert """<th scope="col">Transmitted At</th>""" in response.text
    assert mock_called(uc)
    assert mock_called(ift)


def test_transmisison_status_data_not_authorised(mocker, monkeypatch):
    protect_endpoint()
    client = mock_client(monkeypatch)
    uc = mock_user_check_exists(mocker)
    ift = mock_transmit_role_enabled_false(mocker)
    response = client.get("/transmissions/status/data?page=1&size=10")
    assert response.status_code == 200
    assert """User is not authorised to transmit FHIR messages.""" in response.text
    assert mock_called(uc)
    assert mock_called(ift)
