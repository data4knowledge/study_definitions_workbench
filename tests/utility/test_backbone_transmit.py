import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.configuration.configuration import application_configuration
from app.utility.backbone_transmit import (
    backbone_enabled,
    backbone_headers,
    backbone_load_url,
    backbone_transmit,
    run_backbone_transmit,
    _outcome_message,
)


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    return user


@pytest.fixture
def backbone_url(mocker):
    mocker.patch.object(
        application_configuration, "backbone_url", "http://backbone:8000/"
    )
    mocker.patch.object(application_configuration, "backbone_api_key", None)


def _response(status_code, body=None, text=""):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body
    response.text = text if text else (json.dumps(body) if body else "")
    return response


def _http_client(response):
    """A mock for the httpx.AsyncClient async-context-manager usage."""
    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    client_cls = MagicMock()
    client_cls.return_value.__aenter__ = AsyncMock(return_value=client)
    client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return client_cls, client


class TestConfiguration:
    def test_enabled(self, backbone_url):
        assert backbone_enabled() is True

    def test_disabled(self, mocker):
        mocker.patch.object(application_configuration, "backbone_url", None)
        assert backbone_enabled() is False

    def test_load_url_strips_trailing_slash(self, backbone_url):
        assert backbone_load_url() == "http://backbone:8000/v1/studies"

    def test_headers_with_api_key(self, mocker):
        mocker.patch.object(
            application_configuration, "backbone_api_key", "secret-key"
        )
        assert backbone_headers() == {"X-API-Key": "secret-key"}

    def test_headers_without_api_key(self, mocker):
        mocker.patch.object(application_configuration, "backbone_api_key", None)
        assert backbone_headers() == {}


class TestOutcomeMessage:
    def test_success(self):
        response = _response(
            200,
            {
                "slug": "NCT12345678",
                "study_id": "uuid-1",
                "graph_uri": "urn:usdm:data:NCT12345678",
                "triple_count": 16265,
            },
        )
        success, message = _outcome_message(response)
        assert success is True
        assert "NCT12345678" in message
        assert "16265" in message

    def test_conflict(self):
        success, message = _outcome_message(_response(409, text="exists"))
        assert success is False
        assert "already loaded" in message

    def test_other_failure(self):
        success, message = _outcome_message(_response(422, text="no slug"))
        assert success is False
        assert "HTTP 422" in message
        assert "no slug" in message

    def test_failure_long_message_truncated(self):
        success, message = _outcome_message(_response(400, text="x" * 300))
        assert success is False
        assert "..." in message


class TestBackboneTransmit:
    def _usdm(self, tmp_path):
        usdm_file = tmp_path / "usdm.json"
        usdm_file.write_text('{"study": {}}')
        usdm = MagicMock()
        usdm.study_version.return_value = {"titles": {"C207616": "Study X"}}
        usdm.json.return_value = (str(usdm_file), "usdm.json", "application/json")
        return usdm

    @pytest.mark.asyncio
    @patch("app.utility.backbone_transmit.connection_manager")
    @patch("app.utility.backbone_transmit.Transmission")
    @patch("app.utility.backbone_transmit.USDMJson")
    @patch("app.utility.backbone_transmit.SessionLocal")
    async def test_success(
        self, mock_sl, mock_usdm, mock_tx, mock_cm, mock_user, backbone_url, tmp_path
    ):
        mock_sl.return_value = MagicMock()
        mock_usdm.return_value = self._usdm(tmp_path)
        tx = MagicMock()
        mock_tx.create.return_value = tx
        mock_cm.success = AsyncMock()
        client_cls, client = _http_client(
            _response(
                200,
                {
                    "slug": "NCT12345678",
                    "study_id": "uuid-1",
                    "graph_uri": "urn:usdm:data:NCT12345678",
                    "triple_count": 100,
                },
            )
        )
        with patch("app.utility.backbone_transmit.httpx.AsyncClient", client_cls):
            await backbone_transmit(1, mock_user)
        client.post.assert_awaited_once()
        url = client.post.call_args[0][0]
        assert url == "http://backbone:8000/v1/studies"
        assert "file" in client.post.call_args[1]["files"]
        assert client.post.call_args[1]["headers"] == {}
        tx.update_status.assert_called_once()
        mock_cm.success.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.utility.backbone_transmit.connection_manager")
    @patch("app.utility.backbone_transmit.Transmission")
    @patch("app.utility.backbone_transmit.USDMJson")
    @patch("app.utility.backbone_transmit.SessionLocal")
    async def test_conflict(
        self, mock_sl, mock_usdm, mock_tx, mock_cm, mock_user, backbone_url, tmp_path
    ):
        mock_sl.return_value = MagicMock()
        mock_usdm.return_value = self._usdm(tmp_path)
        tx = MagicMock()
        mock_tx.create.return_value = tx
        mock_cm.error = AsyncMock()
        client_cls, _ = _http_client(_response(409, text="exists"))
        with patch("app.utility.backbone_transmit.httpx.AsyncClient", client_cls):
            await backbone_transmit(1, mock_user)
        tx.update_status.assert_called_once()
        mock_cm.error.assert_awaited_once()
        assert "already loaded" in mock_cm.error.call_args[0][0]

    @pytest.mark.asyncio
    @patch("app.utility.backbone_transmit.connection_manager")
    @patch("app.utility.backbone_transmit.Transmission")
    @patch("app.utility.backbone_transmit.USDMJson")
    @patch("app.utility.backbone_transmit.SessionLocal")
    async def test_exception(
        self, mock_sl, mock_usdm, mock_tx, mock_cm, mock_user, backbone_url
    ):
        session = MagicMock()
        mock_sl.return_value = session
        mock_usdm.side_effect = Exception("boom")
        mock_cm.error = AsyncMock()
        await backbone_transmit(1, mock_user)
        mock_cm.error.assert_awaited_once()
        session.close.assert_called_once()


class TestRunBackboneTransmitThread:
    @patch("app.utility.backbone_transmit.threading.Thread")
    def test_run(self, mock_thread, mock_user):
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        run_backbone_transmit(1, mock_user)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
