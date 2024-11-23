import pytest
from unittest.mock import patch
from app.model.services.address_service import AddressService
from tests.mocks.service_mocks import mock_post
from tests.mocks.general_mocks import mock_called, mock_parameters_correct

@pytest.fixture
def anyio_backend():
  return 'asyncio'

def test_init(monkeypatch):
  monkeypatch.setenv("ADDRESS_SERVER_URL", "http://example.com")
  service = AddressService()
  method_list = [func for func in dir(AddressService) if callable(getattr(AddressService, func))]
  print(f"METHODS: {method_list}")
  assert service.base_url == "http://example.com"

@pytest.mark.asyncio
async def test_parser(mocker, monkeypatch):
  sp = mock_post(mocker)
  monkeypatch.setenv("ADDRESS_SERVER_URL", "http://example.com")
  service = AddressService()
  assert await service.parser('100 main st buffalo ny usa') == {'address': 'address'}
  assert mock_called(sp)
  mock_parameters_correct(sp, [mocker.call('parser', data={'query': '100 main st buffalo ny usa'})])
