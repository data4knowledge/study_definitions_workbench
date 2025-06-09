import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from starlette.datastructures import FormData, UploadFile
from app.imports.form_handler import FormHandler


@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = AsyncMock(spec=Request)
    return request


@pytest.fixture
def mock_form_data():
    """Create a mock form data object."""
    form_data = MagicMock(spec=FormData)
    return form_data


@pytest.fixture
def mock_upload_file():
    """Create a mock upload file."""
    file = MagicMock(spec=UploadFile)
    file.filename = "test.xlsx"
    file.read = AsyncMock(return_value=b"file content")
    return file


@pytest.fixture
def mock_image_file():
    """Create a mock image file."""
    file = MagicMock(spec=UploadFile)
    file.filename = "test.png"
    file.read = AsyncMock(return_value=b"image content")
    return file


@pytest.fixture
def mock_local_files():
    """Mock the LocalFiles class."""
    with patch("app.imports.form_handler.LocalFiles") as mock:
        instance = mock.return_value
        instance.download.return_value = ("test", "xlsx", b"file content")
        yield mock


@pytest.fixture
def mock_pfda_files():
    """Mock the PFDAFiles class."""
    with patch("app.imports.form_handler.PFDAFiles") as mock:
        instance = mock.return_value
        instance.download.return_value = ("test", "xlsx", b"file content")
        yield mock


@pytest.fixture
def mock_logger():
    """Mock the application_logger."""
    with patch("app.imports.form_handler.application_logger") as mock:
        yield mock


class TestFormHandler:
    """Tests for the FormHandler class."""

    def test_init(self):
        """Test initialization of FormHandler."""
        request = MagicMock(spec=Request)
        handler = FormHandler(request, True, ".xlsx", "browser")

        assert handler.request == request
        assert handler.image_files is True
        assert handler.ext == ".xlsx"
        assert handler.source == "browser"
        assert "browser" in handler._files_method
        assert "pfda" in handler._files_method
        assert "os" in handler._files_method

    def test_init_with_ext_without_dot(self):
        """Test initialization with extension without dot."""
        request = MagicMock(spec=Request)
        handler = FormHandler(request, True, "xlsx", "browser")

        assert handler.ext == ".xlsx"

    @pytest.mark.parametrize(
        "file_extension, is_main_file, is_image_file, expected_message",
        [
            (".xlsx", True, False, "File 'test.xlsx' accepted"),
            (".png", False, True, "Image file 'test.png' accepted"),
            (
                ".txt",
                False,
                False,
                "File 'test.txt' was ignored, not '.xlsx' file or image file",
            ),
            (".txt", False, False, "File 'test.txt' was ignored, not '.xlsx' file"),
        ],
    )
    def test_handle_file(
        self, file_extension, is_main_file, is_image_file, expected_message, mock_logger
    ):
        """Test _handle_file method with different file types."""
        request = MagicMock(spec=Request)
        handler = FormHandler(request, is_image_file, ".xlsx", "browser")

        messages = []
        main_file = (
            None
            if not is_main_file
            else {"filename": "existing.xlsx", "contents": b"existing content"}
        )
        image_files = []

        result_main_file, result_image_files = handler._handle_file(
            file_extension,
            "test",
            f"test{file_extension}",
            b"file content",
            messages,
            main_file,
            image_files,
        )

        # Check messages
        if file_extension == ".xlsx":
            assert messages == ["File 'test.xlsx' accepted"]
            assert result_main_file == {
                "filename": "test.xlsx",
                "contents": b"file content",
            }
            assert result_image_files == []
            mock_logger.info.assert_called_once_with("Processing upload file 'test'")
        elif file_extension == ".png" and is_image_file:
            assert messages == ["Image file 'test.png' accepted"]
            assert result_main_file == main_file
            assert result_image_files == [
                {"filename": "test.png", "contents": b"file content"}
            ]
            mock_logger.info.assert_called_once_with("Processing upload file 'test'")
        else:
            assert messages[0].startswith("File 'test.txt' was ignored")
            assert result_main_file == main_file
            assert result_image_files == []
            mock_logger.info.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_files_browser(
        self, mock_request, mock_upload_file, mock_image_file, mock_logger
    ):
        """Test _get_files_browser method."""
        # Setup
        form = MagicMock()
        form.getlist.return_value = [mock_upload_file, mock_image_file]
        mock_request.form.return_value = form

        handler = FormHandler(mock_request, True, ".xlsx", "browser")

        # Execute
        main_file, image_files, messages = await handler._get_files_browser(form)

        # Assert
        assert main_file == {"filename": "test.xlsx", "contents": b"file content"}
        assert len(image_files) == 1
        assert image_files[0] == {"filename": "test.png", "contents": b"image content"}
        assert len(messages) == 2
        assert messages[0] == "File 'test.xlsx' accepted"
        assert messages[1] == "Image file 'test.png' accepted"
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_files_os(self, mock_request, mock_local_files, mock_logger):
        """Test _get_files_os method."""
        # Setup
        form = MagicMock()
        form.getlist.return_value = ['["file1", "file2"]']
        mock_request.form.return_value = form

        # Mock json.loads to return a list of file paths
        with patch("json.loads", return_value=["file1", "file2"]):
            # Mock _handle_file to return the expected values
            with patch.object(FormHandler, "_handle_file") as mock_handle_file:
                mock_handle_file.return_value = (
                    {"filename": "test.xlsx", "contents": b"file content"},
                    [],
                )

                handler = FormHandler(mock_request, True, ".xlsx", "os")

                # Execute
                main_file, image_files, messages = await handler._get_files_os(form)

                # Assert
                assert main_file == {
                    "filename": "test.xlsx",
                    "contents": b"file content",
                }
                assert image_files == []
                assert mock_handle_file.call_count == 2

    @pytest.mark.asyncio
    async def test_get_files_pfda(self, mock_request, mock_pfda_files, mock_logger):
        """Test _get_files_pfda method."""
        # Setup
        form = MagicMock()
        form.getlist.return_value = ['["file1", "file2"]']
        mock_request.form.return_value = form

        # Mock json.loads to return a list of file paths
        with patch("json.loads", return_value=["file1", "file2"]):
            # Mock _handle_file to return the expected values
            with patch.object(FormHandler, "_handle_file") as mock_handle_file:
                mock_handle_file.return_value = (
                    {"filename": "test.xlsx", "contents": b"file content"},
                    [],
                )

                handler = FormHandler(mock_request, True, ".xlsx", "pfda")

                # Execute
                main_file, image_files, messages = await handler._get_files_pfda(form)

                # Assert
                assert main_file == {
                    "filename": "test.xlsx",
                    "contents": b"file content",
                }
                assert image_files == []
                assert mock_handle_file.call_count == 2

    @pytest.mark.asyncio
    async def test_get_files(self, mock_request):
        """Test get_files method."""
        # Setup
        form = MagicMock()
        mock_request.form = AsyncMock(return_value=form)

        # Create a handler with a mocked _get_files_browser method
        with patch.object(
            FormHandler, "_get_files_browser", new_callable=AsyncMock
        ) as mock_get_files:
            mock_get_files.return_value = ({"filename": "test.xlsx"}, [], ["message"])

            handler = FormHandler(mock_request, True, ".xlsx", "browser")

            # Execute
            main_file, image_files, messages = await handler.get_files()

            # Assert
            assert main_file == {"filename": "test.xlsx"}
            assert image_files == []
            assert messages == ["message"]
            mock_get_files.assert_called_once_with(form)
