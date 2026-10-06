from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.utility.fhir_service import FHIRService


@pytest.fixture
def fhir_service():
    with patch("app.utility.service.httpx.AsyncClient"):
        svc = FHIRService("https://fhir.example.com")
    return svc


@pytest.fixture
def fhir_service_auth():
    with patch("app.utility.service.httpx.AsyncClient"):
        svc = FHIRService("https://fhir.example.com", auth=("user", "pass"))
    return svc


class TestFHIRServiceInit:
    def test_init(self):
        with patch("app.utility.service.httpx.AsyncClient"):
            svc = FHIRService("https://fhir.example.com")
        assert svc.base_url == "https://fhir.example.com"
        assert svc._auth is None

    def test_init_with_auth(self):
        with patch("app.utility.service.httpx.AsyncClient"):
            svc = FHIRService("https://fhir.example.com", auth=("u", "p"))
        assert svc._auth == ("u", "p")


class TestFHIRServicePut:
    @pytest.mark.asyncio
    async def test_put_success_200(self, fhir_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "bundle-1"}'
        fhir_service._client.put = AsyncMock(return_value=mock_response)
        result = await fhir_service.put("/Bundle", data='{"data": "test"}')
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_put_success_201(self, fhir_service):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"id": "bundle-2"}'
        fhir_service._client.put = AsyncMock(return_value=mock_response)
        result = await fhir_service.put("/Bundle", data='{"data": "test"}')
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_put_failure(self, fhir_service):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        fhir_service._client.put = AsyncMock(return_value=mock_response)
        result = await fhir_service.put("/Bundle")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_put_exception(self, fhir_service):
        fhir_service._client.put = AsyncMock(side_effect=httpx.HTTPError("timeout"))
        result = await fhir_service.put("/Bundle")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_put_sends_auth_when_given(self, fhir_service_auth):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "bundle-3"}'
        fhir_service_auth._client.put = AsyncMock(return_value=mock_response)
        await fhir_service_auth.put("/Bundle")
        call_kwargs = fhir_service_auth._client.put.call_args[1]
        assert call_kwargs["auth"] == ("user", "pass")

    @pytest.mark.asyncio
    async def test_put_sends_no_auth_when_not_given(self, fhir_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "bundle-4"}'
        fhir_service._client.put = AsyncMock(return_value=mock_response)
        await fhir_service.put("/Bundle")
        call_kwargs = fhir_service._client.put.call_args[1]
        assert "auth" not in call_kwargs


class TestFHIRServiceWrappers:
    @pytest.mark.asyncio
    async def test_bundle_list(self, fhir_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"resourceType": "Bundle"}'
        fhir_service._client.get = AsyncMock(return_value=mock_response)
        result = await fhir_service.bundle_list()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get(self, fhir_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"resourceType": "Patient"}'
        fhir_service._client.get = AsyncMock(return_value=mock_response)
        result = await fhir_service.get("/Patient/1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_post(self, fhir_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "1"}'
        fhir_service._client.post = AsyncMock(return_value=mock_response)
        result = await fhir_service.post("/Bundle", data='{"data": "test"}')
        assert result["success"] is True
