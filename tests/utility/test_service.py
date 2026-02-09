import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from app.utility.service import Service


@pytest.fixture
def service():
    with patch("app.utility.service.httpx.AsyncClient"):
        svc = Service("https://api.example.com")
    return svc


class TestServiceInit:
    def test_strips_trailing_slash(self):
        with patch("app.utility.service.httpx.AsyncClient"):
            svc = Service("https://api.example.com/")
        assert svc.base_url == "https://api.example.com"

    def test_no_trailing_slash(self):
        with patch("app.utility.service.httpx.AsyncClient"):
            svc = Service("https://api.example.com")
        assert svc.base_url == "https://api.example.com"


class TestServiceGet:
    @pytest.mark.asyncio
    async def test_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"result": "ok"}'
        service._client.get = AsyncMock(return_value=mock_response)
        result = await service.get("/test")
        assert result["success"] is True
        assert result["data"] == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_failure(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        service._client.get = AsyncMock(return_value=mock_response)
        result = await service.get("/test")
        assert result["success"] is False
        assert result["status"] == 404

    @pytest.mark.asyncio
    async def test_exception(self, service):
        service._client.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))
        result = await service.get("/test")
        assert result["success"] is False
        assert "HTTPError" in result["message"]


class TestServicePost:
    @pytest.mark.asyncio
    async def test_success_200(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": 1}'
        service._client.post = AsyncMock(return_value=mock_response)
        result = await service.post("/test", data='{"key": "val"}')
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_success_201(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"id": 1}'
        service._client.post = AsyncMock(return_value=mock_response)
        result = await service.post("/test")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_failure(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        service._client.post = AsyncMock(return_value=mock_response)
        result = await service.post("/test")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_exception(self, service):
        service._client.post = AsyncMock(side_effect=httpx.HTTPError("fail"))
        result = await service.post("/test")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_custom_timeout(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"ok": true}'
        service._client.post = AsyncMock(return_value=mock_response)
        result = await service.post("/test", timeout=30.0)
        assert result["success"] is True
        call_kwargs = service._client.post.call_args[1]
        assert call_kwargs["timeout"] == 30.0


class TestServiceFilePost:
    @pytest.mark.asyncio
    async def test_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"uploaded": true}'
        service._client.post = AsyncMock(return_value=mock_response)
        result = await service.file_post("/upload", files={"file": b"data"})
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_with_data(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = '{"uploaded": true}'
        service._client.post = AsyncMock(return_value=mock_response)
        result = await service.file_post(
            "/upload", files={"file": b"data"}, data={"name": "test"}
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_failure(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error"
        service._client.post = AsyncMock(return_value=mock_response)
        result = await service.file_post("/upload", files={"file": b"data"})
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_exception(self, service):
        service._client.post = AsyncMock(side_effect=httpx.HTTPError("fail"))
        result = await service.file_post("/upload", files={"file": b"data"})
        assert result["success"] is False


class TestServiceDelete:
    @pytest.mark.asyncio
    async def test_success(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.text = '""'
        service._client.delete = AsyncMock(return_value=mock_response)
        result = await service.delete("/test/1")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_failure(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        service._client.delete = AsyncMock(return_value=mock_response)
        result = await service.delete("/test/1")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_exception(self, service):
        service._client.delete = AsyncMock(side_effect=httpx.HTTPError("fail"))
        result = await service.delete("/test/1")
        assert result["success"] is False


class TestServiceStatus:
    @pytest.mark.asyncio
    async def test_status(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "ok"}'
        service._client.get = AsyncMock(return_value=mock_response)
        result = await service.status()
        assert result["success"] is True


class TestServiceFullUrl:
    def test_with_slash(self, service):
        assert service._full_url("/path") == "https://api.example.com/path"

    def test_without_slash(self, service):
        assert service._full_url("path") == "https://api.example.com/path"
