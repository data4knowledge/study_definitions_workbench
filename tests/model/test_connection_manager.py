import pytest
from unittest.mock import AsyncMock, patch
from app.model.connection_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_ws():
    ws = AsyncMock()
    return ws


class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_ws):
        await manager.connect("user1", mock_ws)
        mock_ws.accept.assert_awaited_once()
        assert "user1" in manager.active_connections

    def test_disconnect(self, manager, mock_ws):
        manager.active_connections["user1"] = mock_ws
        manager.disconnect("user1")
        assert "user1" not in manager.active_connections

    def test_disconnect_nonexistent(self, manager):
        manager.disconnect("nonexistent")  # should not raise

    @pytest.mark.asyncio
    async def test_success_with_connection(self, manager, mock_ws):
        manager.active_connections["user1"] = mock_ws
        await manager.success("It worked", "user1")
        mock_ws.send_text.assert_awaited_once()
        call_arg = mock_ws.send_text.call_args[0][0]
        assert "success" in call_arg
        assert "It worked" in call_arg

    @pytest.mark.asyncio
    @patch("app.model.connection_manager.application_logger")
    async def test_success_no_connection(self, mock_logger, manager):
        await manager.success("msg", "unknown_user")
        mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_warning_with_connection(self, manager, mock_ws):
        manager.active_connections["user1"] = mock_ws
        await manager.warning("Watch out", "user1")
        mock_ws.send_text.assert_awaited_once()
        call_arg = mock_ws.send_text.call_args[0][0]
        assert "warning" in call_arg

    @pytest.mark.asyncio
    async def test_error_with_connection(self, manager, mock_ws):
        manager.active_connections["user1"] = mock_ws
        await manager.error("Something broke", "user1")
        mock_ws.send_text.assert_awaited_once()
        call_arg = mock_ws.send_text.call_args[0][0]
        assert "danger" in call_arg

    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.active_connections["u1"] = ws1
        manager.active_connections["u2"] = ws2
        await manager.broadcast("Alert everyone")
        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_awaited_once()

    def test_to_html(self, manager):
        html = manager._to_html("u1", "Success:", "success", "Done!")
        assert "alert-success" in html
        assert "Done!" in html
        assert "Success:" in html
