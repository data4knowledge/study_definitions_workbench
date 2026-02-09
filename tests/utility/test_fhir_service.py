import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from app.utility.fhir_service import FHIRService


@pytest.fixture
def fhir_service():
    with (
        patch("app.utility.fhir_service.ServiceEnvironment") as mock_se,
        patch("app.utility.service.httpx.AsyncClient"),
    ):
        mock_se_instance = MagicMock()
        mock_se_instance.get.side_effect = lambda k: {
            "ENDPOINT_USERNAME": "user",
            "ENDPOINT_PASSWORD": "pass",
        }.get(k, "")
        mock_se.return_value = mock_se_instance
        svc = FHIRService("https://fhir.example.com")
    return svc


class TestFHIRServiceInit:
    def test_init(self):
        with (
            patch("app.utility.fhir_service.ServiceEnvironment") as mock_se,
            patch("app.utility.service.httpx.AsyncClient"),
        ):
            svc = FHIRService("https://fhir.example.com")
        assert svc.base_url == "https://fhir.example.com"
        assert svc._se is not None


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
    async def test_put_uses_auth(self, fhir_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "bundle-3"}'
        fhir_service._client.put = AsyncMock(return_value=mock_response)
        await fhir_service.put("/Bundle")
        call_kwargs = fhir_service._client.put.call_args[1]
        assert call_kwargs["auth"] == ("user", "pass")


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
