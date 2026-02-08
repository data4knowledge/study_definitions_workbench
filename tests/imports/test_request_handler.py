import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.imports.request_handler import RequestHandler


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestRequestHandler:

    def test_init(self):
        handler = RequestHandler("M11_DOCX", "browser")
        assert handler.type == "M11_DOCX"
        assert handler.source == "browser"

    @pytest.mark.asyncio
    async def test_process_success(self):
        handler = RequestHandler("M11_DOCX", "browser")
        mock_request = MagicMock()
        mock_templates = MagicMock()
        mock_templates.TemplateResponse.return_value = "success_response"
        mock_user = MagicMock()
        with patch("app.imports.request_handler.ImportManager") as mock_im, \
             patch("app.imports.request_handler.FormHandler") as mock_fh, \
             patch("app.imports.request_handler.execute_import"):
            mock_im_instance = mock_im.return_value
            mock_im_instance.images = False
            mock_im_instance.main_file_ext = ".docx"
            mock_fh_instance = mock_fh.return_value
            mock_fh_instance.get_files = AsyncMock(return_value=(
                {"filename": "test.docx", "contents": b"data"},
                [],
                ["File accepted"],
            ))
            mock_im_instance.save_files.return_value = "test-uuid"
            result = await handler.process(mock_request, mock_templates, mock_user)
        assert result == "success_response"
        mock_templates.TemplateResponse.assert_called_once()
        call_args = mock_templates.TemplateResponse.call_args
        assert call_args[0][0] == "import/partials/upload_success.html"

    @pytest.mark.asyncio
    async def test_process_no_uuid(self):
        handler = RequestHandler("M11_DOCX", "browser")
        mock_request = MagicMock()
        mock_templates = MagicMock()
        mock_templates.TemplateResponse.return_value = "fail_response"
        mock_user = MagicMock()
        with patch("app.imports.request_handler.ImportManager") as mock_im, \
             patch("app.imports.request_handler.FormHandler") as mock_fh:
            mock_im_instance = mock_im.return_value
            mock_im_instance.images = False
            mock_im_instance.main_file_ext = ".docx"
            mock_fh_instance = mock_fh.return_value
            mock_fh_instance.get_files = AsyncMock(return_value=(
                {"filename": "test.docx", "contents": b"data"},
                [],
                [],
            ))
            mock_im_instance.save_files.return_value = None
            result = await handler.process(mock_request, mock_templates, mock_user)
        assert result == "fail_response"
        call_args = mock_templates.TemplateResponse.call_args
        assert call_args[0][0] == "import/partials/upload_fail.html"

    @pytest.mark.asyncio
    async def test_process_exception(self):
        handler = RequestHandler("M11_DOCX", "browser")
        mock_request = MagicMock()
        mock_templates = MagicMock()
        mock_templates.TemplateResponse.return_value = "exception_response"
        mock_user = MagicMock()
        with patch("app.imports.request_handler.ImportManager") as mock_im:
            mock_im.side_effect = Exception("test error")
            result = await handler.process(mock_request, mock_templates, mock_user)
        assert result == "exception_response"
        call_args = mock_templates.TemplateResponse.call_args
        assert call_args[0][0] == "import/partials/upload_fail.html"
