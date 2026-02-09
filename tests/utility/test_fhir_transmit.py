import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.utility.fhir_transmit import (
    fhir_m11_transmit,
    fhir_soa_transmit,
    fhir_transmit,
    run_fhir_m11_transmit,
    run_fhir_soa_transmit,
)


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    return user


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.close = MagicMock()
    return session


class TestFhirM11Transmit:
    @pytest.mark.asyncio
    @patch("app.utility.fhir_transmit.fhir_transmit", new_callable=AsyncMock)
    @patch("app.utility.fhir_transmit.USDMJson")
    @patch("app.utility.fhir_transmit.SessionLocal")
    async def test_fhir_m11_transmit(
        self, mock_session_local, mock_usdm, mock_ft, mock_user
    ):
        mock_session_local.return_value = MagicMock()
        mock_usdm_instance = MagicMock()
        mock_usdm_instance.study_version.return_value = {
            "titles": {"C207616": "Test"}
        }
        mock_usdm_instance.fhir_data.return_value = '{"data": "fhir"}'
        mock_usdm.return_value = mock_usdm_instance
        await fhir_m11_transmit(1, 2, "prism2", mock_user)
        mock_ft.assert_awaited_once()


class TestFhirSoaTransmit:
    @pytest.mark.asyncio
    @patch("app.utility.fhir_transmit.fhir_transmit", new_callable=AsyncMock)
    @patch("app.utility.fhir_transmit.USDMJson")
    @patch("app.utility.fhir_transmit.SessionLocal")
    async def test_fhir_soa_transmit(
        self, mock_session_local, mock_usdm, mock_ft, mock_user
    ):
        mock_session_local.return_value = MagicMock()
        mock_usdm_instance = MagicMock()
        mock_usdm_instance.study_version.return_value = {}
        mock_usdm_instance.fhir_soa_data.return_value = '{"soa": "data"}'
        mock_usdm.return_value = mock_usdm_instance
        await fhir_soa_transmit(1, 2, "timeline-1", mock_user)
        mock_ft.assert_awaited_once()


class TestFhirTransmit:
    @pytest.mark.asyncio
    @patch("app.utility.fhir_transmit.connection_manager")
    @patch("app.utility.fhir_transmit.FHIRService")
    @patch("app.utility.fhir_transmit.Endpoint")
    @patch("app.utility.fhir_transmit.Transmission")
    async def test_success(
        self, mock_tx, mock_ep, mock_fhir, mock_cm, mock_user, mock_session
    ):
        mock_tx.create.return_value = MagicMock()
        mock_ep.find.return_value = MagicMock(endpoint="https://fhir.test/api")
        mock_server = MagicMock()
        mock_server.put = AsyncMock(
            return_value={"success": True, "data": {"id": "bundle-123"}}
        )
        mock_fhir.return_value = mock_server
        mock_cm.success = AsyncMock()

        details = {"titles": {"C207616": "Study X"}}
        await fhir_transmit(
            "M11", 1, 2, '{"data": "test"}', details, mock_user, mock_session
        )

        mock_cm.success.assert_awaited_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.utility.fhir_transmit.connection_manager")
    @patch("app.utility.fhir_transmit.FHIRService")
    @patch("app.utility.fhir_transmit.Endpoint")
    @patch("app.utility.fhir_transmit.Transmission")
    async def test_failure(
        self, mock_tx, mock_ep, mock_fhir, mock_cm, mock_user, mock_session
    ):
        mock_tx.create.return_value = MagicMock()
        mock_ep.find.return_value = MagicMock(endpoint="https://fhir.test/api")
        mock_server = MagicMock()
        mock_server.put = AsyncMock(
            return_value={"success": False, "message": "Bad request"}
        )
        mock_fhir.return_value = mock_server
        mock_cm.error = AsyncMock()

        details = {"titles": {"C207616": "Study X"}}
        await fhir_transmit(
            "M11", 1, 2, '{"data": "test"}', details, mock_user, mock_session
        )

        mock_cm.error.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("app.utility.fhir_transmit.connection_manager")
    @patch("app.utility.fhir_transmit.FHIRService")
    @patch("app.utility.fhir_transmit.Endpoint")
    @patch("app.utility.fhir_transmit.Transmission")
    async def test_failure_long_message(
        self, mock_tx, mock_ep, mock_fhir, mock_cm, mock_user, mock_session
    ):
        mock_tx.create.return_value = MagicMock()
        mock_ep.find.return_value = MagicMock(endpoint="https://fhir.test/api")
        long_msg = "x" * 200
        mock_server = MagicMock()
        mock_server.put = AsyncMock(
            return_value={"success": False, "message": long_msg}
        )
        mock_fhir.return_value = mock_server
        mock_cm.error = AsyncMock()

        details = {"titles": {"C207616": "Study X"}}
        await fhir_transmit(
            "M11", 1, 2, '{"data": "test"}', details, mock_user, mock_session
        )

        call_arg = mock_cm.error.call_args[0][0]
        assert "..." in call_arg

    @pytest.mark.asyncio
    @patch("app.utility.fhir_transmit.connection_manager")
    @patch("app.utility.fhir_transmit.Transmission")
    async def test_exception(self, mock_tx, mock_cm, mock_user, mock_session):
        mock_tx.create.side_effect = Exception("DB error")
        mock_cm.error = AsyncMock()

        details = {"titles": {"C207616": "Study X"}}
        await fhir_transmit(
            "M11", 1, 2, '{"data": "test"}', details, mock_user, mock_session
        )

        mock_cm.error.assert_awaited_once()
        mock_session.close.assert_called_once()


class TestRunFhirTransmitThreads:
    @patch("app.utility.fhir_transmit.threading.Thread")
    def test_run_m11(self, mock_thread, mock_user):
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        run_fhir_m11_transmit(1, 2, "prism2", mock_user)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

    @patch("app.utility.fhir_transmit.threading.Thread")
    def test_run_soa(self, mock_thread, mock_user):
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        run_fhir_soa_transmit(1, 2, "timeline-1", mock_user)
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
