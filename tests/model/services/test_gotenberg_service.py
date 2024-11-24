import pytest
from unittest.mock import patch
from app.model.services.gotenberg_service import GotenbergService
from tests.mocks.service_mocks import mock_get
from tests.mocks.general_mocks import mock_called, mock_parameters_correct

@pytest.fixture
def anyio_backend():
  return 'asyncio'

def test_init(monkeypatch):
  monkeypatch.setenv("GOTENBERG_SERVER_URL", "http://example.com")
  service = GotenbergService()
  assert service.base_url == "http://example.com"

@pytest.mark.asyncio
async def test_health(mocker, monkeypatch):
  sg = mock_get(mocker, {"status": "healthy"})
  monkeypatch.setenv("GOTENBERG_SERVER_URL", "http://example.com")
  service = GotenbergService()
  assert await service.health() == {"status": "healthy"}
  assert mock_called(sg)
  mock_parameters_correct(sg, [mocker.call('/health')])

@pytest.mark.asyncio
async def test_docx_to_pdf(mocker, monkeypatch):
  sp = mock_file_post(mocker)
  monkeypatch.setenv("GOTENBERG_SERVER_URL", "http://example.com")
  service = GotenbergService()
  assert await service.docx_to_pdf('tests/test_files/m11/LZZT/LZZT.docx', 'output.pdf') == {'address': 'address'}
  assert mock_called(sp)
  mock_parameters_correct(sp, [mocker.call('/forms/libreoffice/convert', {'files': ('LZZT.docx', 'xxx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}, {'landscape': 'false', 'paperWidth': 8.27, 'paperHeight': 11.7})])

def mock_file_post(mocker):
  mock = mocker.patch(f"app.model.services.gotenberg_service.GotenbergService._file_post")
  mock.side_effect = [{'address': 'address'}]
  return mock
