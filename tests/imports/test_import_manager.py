import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.imports.import_manager import ImportManager, execute_import
from app.database.user import User
from app.imports.import_processors import (
    ImportExcel,
    ImportM11,
    ImportFhirPRISM2,
    ImportUSDM3,
    ImportUSDM4,
)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return MagicMock(spec=User, id=1)


@pytest.fixture
def mock_data_files():
    """Mock the DataFiles class."""
    with patch("app.imports.import_manager.DataFiles") as mock:
        instance = mock.return_value
        instance.new.return_value = "test-uuid"
        instance.save.return_value = ("/path/to/file", "filename.ext")
        instance.path.return_value = ("/path/to/file", "filename.ext", True)
        yield mock


@pytest.fixture
def mock_session_local():
    """Mock the SessionLocal."""
    with patch("app.imports.import_manager.SessionLocal") as mock:
        session = MagicMock()
        mock.return_value = session
        yield mock


@pytest.fixture
def mock_file_import():
    """Mock the FileImport class."""
    with patch("app.imports.import_manager.FileImport") as mock:
        instance = mock.return_value
        mock.create.return_value = instance
        yield mock


@pytest.fixture
def mock_study():
    """Mock the Study class."""
    with patch("app.imports.import_manager.Study") as mock:
        mock.study_and_version.return_value = (MagicMock(), True)
        yield mock


@pytest.fixture
def mock_connection_manager():
    """Mock the connection_manager."""
    with patch("app.imports.import_manager.connection_manager") as mock:
        mock.success = AsyncMock()
        mock.error = AsyncMock()
        yield mock


@pytest.fixture
def mock_import_processor():
    """Mock the import processor."""
    with patch("app.imports.import_processors.ImportProcessorBase") as mock:
        instance = mock.return_value
        instance.process = AsyncMock()
        instance.process.return_value = {
            "name": "test-study",
            "phase": "Phase 1",
            "full_title": "Test Study Title",
            "sponsor_identifier": "TEST-123",
            "nct_identifier": "NCT12345678",
            "sponsor": "Test Sponsor",
        }
        instance.usdm = '{"study": {"name": "test-study"}}'
        instance.errors = None
        instance.extra = {}
        yield mock


@pytest.fixture
def mock_logger():
    """Mock the application_logger."""
    with patch("app.imports.import_manager.application_logger") as mock:
        yield mock


class TestImportManager:
    """Tests for the ImportManager class."""

    def test_init(self, mock_user):
        """Test initialization of ImportManager."""
        # Test with USDM_EXCEL
        manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
        assert manager.user == mock_user
        assert manager.type == ImportManager.USDM_EXCEL
        assert manager.processor == ImportExcel
        assert manager.main_file_type == "xlsx"
        assert manager.main_file_ext == ".xlsx"
        assert manager.images is True
        assert manager.files is None
        assert manager.uuid is None

        # Test with M11_DOCX
        manager = ImportManager(mock_user, ImportManager.M11_DOCX)
        assert manager.user == mock_user
        assert manager.type == ImportManager.M11_DOCX
        assert manager.processor == ImportM11
        assert manager.main_file_type == "docx"
        assert manager.main_file_ext == ".docx"
        assert manager.images is False

        # Test with FHIR_V1_JSON
        manager = ImportManager(mock_user, ImportManager.FHIR_PRISM2_JSON)
        assert manager.user == mock_user
        assert manager.type == ImportManager.FHIR_PRISM2_JSON
        assert manager.processor == ImportFhirPRISM2
        assert manager.main_file_type == "fhir_prism2"
        assert manager.main_file_ext == ".json"
        assert manager.images is False

        # Test with USDM3_JSON
        manager = ImportManager(mock_user, ImportManager.USDM3_JSON)
        assert manager.user == mock_user
        assert manager.type == ImportManager.USDM3_JSON
        assert manager.processor == ImportUSDM3
        assert manager.main_file_type == "usdm"
        assert manager.main_file_ext == ".json"
        assert manager.images is False

        # Test with USDM_JSON
        manager = ImportManager(mock_user, ImportManager.USDM4_JSON)
        assert manager.user == mock_user
        assert manager.type == ImportManager.USDM4_JSON
        assert manager.processor == ImportUSDM4
        assert manager.main_file_type == "usdm"
        assert manager.main_file_ext == ".json"
        assert manager.images is False

    def test_file_types(self):
        assert ImportManager.is_m11_docx_import("M11_DOCX")
        assert ImportManager.is_usdm_excel_import("USDM_EXCEL")
        assert ImportManager.is_fhir_v1_import("FHIR_V1_JSON")
        assert ImportManager.is_usdm3_json_import("USDM3_JSON")
        assert ImportManager.is_usdm4_json_import("USDM4_JSON")
        assert not ImportManager.is_m11_docx_import("USDM_EXCEL")
        assert not ImportManager.is_usdm_excel_import("M11_DOCX")
        assert not ImportManager.is_fhir_v1_import("USDM3_JSON")
        assert not ImportManager.is_usdm3_json_import("FHIR_V1_JSON")
        assert not ImportManager.is_usdm4_json_import("USDM_EXCEL")

    @classmethod
    def is_usdm_excel_import(cls, value: str) -> bool:
        return value == cls.USDM_EXCEL

    @classmethod
    def is_fhir_v1_import(cls, value: str) -> bool:
        return value == cls.FHIR_V1_JSON

    @classmethod
    def is_usdm3_json_import(cls, value: str) -> bool:
        return value == cls.USDM3_JSON

    @classmethod
    def is_usdm4_json_import(cls, value: str) -> bool:
        return value == cls.USDM4_JSON
        """Test file types."""
        assert ImportManager.USDM_EXCEL == "USDM_EXCEL"
        assert ImportManager.M11_DOCX == "M11_DOCX"
        assert ImportManager.FHIR_PRISM2_JSON == "FHIR_V1_JSON"
        assert ImportManager.USDM3_JSON == "USDM3_JSON"
        assert ImportManager.USDM4_JSON == "USDM4_JSON"

    def test_save_files(self, mock_user, mock_data_files):
        """Test save_files method."""
        # Setup
        manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
        main_file = {"filename": "test.xlsx", "contents": b"file content"}
        image_files = [
            {"filename": "image1.png", "contents": b"image1 content"},
            {"filename": "image2.png", "contents": b"image2 content"},
        ]

        # Execute
        uuid = manager.save_files(main_file, image_files)

        # Assert
        assert uuid == "test-uuid"
        assert manager.files is not None
        assert manager.uuid == "test-uuid"
        manager.files.new.assert_called_once()
        assert manager.files.save.call_count == 3
        manager.files.save.assert_any_call("xlsx", b"file content", "test.xlsx")
        manager.files.save.assert_any_call("image", b"image1 content", "image1.png")
        manager.files.save.assert_any_call("image", b"image2 content", "image2.png")

    def test_save_files_no_main_file(self, mock_user, mock_data_files):
        """Test save_files method with no main file."""
        # Setup
        manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
        main_file = None
        image_files = []

        # Execute
        uuid = manager.save_files(main_file, image_files)

        # Assert
        assert uuid is None
        assert manager.files is None
        assert manager.uuid is None
        mock_data_files.return_value.new.assert_not_called()
        mock_data_files.return_value.save.assert_not_called()

    def test_save_files_with_main_file_no_images(self, mock_user, mock_data_files):
        """Test save_files method with main file but no images."""
        # Setup
        manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
        main_file = {"filename": "test.xlsx", "contents": b"file content"}
        image_files = []

        # Execute
        uuid = manager.save_files(main_file, image_files)

        # Assert
        assert uuid == "test-uuid"
        assert manager.files is not None
        assert manager.uuid == "test-uuid"
        manager.files.new.assert_called_once()
        manager.files.save.assert_called_once_with("xlsx", b"file content", "test.xlsx")

    @pytest.mark.asyncio
    async def test_process_success(
        self,
        mock_user,
        mock_data_files,
        mock_session_local,
        mock_file_import,
        mock_study,
        mock_connection_manager,
        mock_import_processor,
    ):
        """Test process method with successful execution."""
        # Setup
        with patch(
            "app.imports.import_manager.ImportExcel",
            return_value=mock_import_processor.return_value,
        ):
            manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
            manager.files = mock_data_files.return_value
            manager.uuid = "test-uuid"

            # Execute
            await manager.process()

            # Assert
            mock_session_local.assert_called_once()
            mock_file_import.create.assert_called_once()
            mock_import_processor.return_value.process.assert_called_once()
            manager.files.save.assert_any_call(
                "usdm", mock_import_processor.return_value.usdm
            )
            manager.files.save.assert_any_call(
                "extra", mock_import_processor.return_value.extra
            )
            mock_study.study_and_version.assert_called_once()
            mock_file_import.return_value.update_status.assert_any_call(
                "Saving", mock_session_local.return_value
            )
            mock_file_import.return_value.update_status.assert_any_call(
                "Create", mock_session_local.return_value
            )
            mock_file_import.return_value.update_status.assert_any_call(
                "Success", mock_session_local.return_value
            )
            mock_connection_manager.success.assert_called_once_with(
                "Import of 'filename.ext' completed sucessfully", str(mock_user.id)
            )
            mock_session_local.return_value.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_errors(
        self,
        mock_user,
        mock_data_files,
        mock_session_local,
        mock_file_import,
        mock_study,
        mock_connection_manager,
        mock_import_processor,
    ):
        """Test process method with errors."""
        # Setup
        with patch(
            "app.imports.import_manager.ImportExcel",
            return_value=mock_import_processor.return_value,
        ):
            manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
            manager.files = mock_data_files.return_value
            manager.uuid = "test-uuid"
            mock_import_processor.return_value.errors = [{"message": "Error message"}]

            # Execute
            await manager.process()

            # Assert
            mock_session_local.assert_called_once()
            mock_file_import.create.assert_called_once()
            mock_import_processor.return_value.process.assert_called_once()
            manager.files.save.assert_any_call(
                "errors", mock_import_processor.return_value.errors
            )
            manager.files.save.assert_any_call(
                "usdm", mock_import_processor.return_value.usdm
            )
            manager.files.save.assert_any_call(
                "extra", mock_import_processor.return_value.extra
            )
            mock_study.study_and_version.assert_called_once()
            mock_file_import.return_value.update_status.assert_any_call(
                "Saving", mock_session_local.return_value
            )
            mock_file_import.return_value.update_status.assert_any_call(
                "Create", mock_session_local.return_value
            )
            mock_file_import.return_value.update_status.assert_any_call(
                "Success", mock_session_local.return_value
            )
            mock_connection_manager.success.assert_called_once_with(
                "Import of 'filename.ext' completed sucessfully", str(mock_user.id)
            )
            mock_session_local.return_value.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_exception(
        self,
        mock_user,
        mock_data_files,
        mock_session_local,
        mock_file_import,
        mock_connection_manager,
        mock_logger,
    ):
        """Test process method with exception."""
        # Setup
        with patch("app.imports.import_manager.ImportExcel") as mock_processor:
            mock_processor.return_value.process.side_effect = Exception(
                "Test exception"
            )
            manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
            manager.files = mock_data_files.return_value
            manager.uuid = "test-uuid"

            # Execute
            await manager.process()

            # Assert
            mock_session_local.assert_called_once()
            mock_file_import.create.assert_called_once()
            mock_file_import.return_value.update_status.assert_called_once_with(
                "Exception", mock_session_local.return_value
            )
            mock_logger.exception.assert_called_once()
            mock_connection_manager.error.assert_called_once_with(
                "Exception encountered importing 'filename.ext'", str(mock_user.id)
            )
            mock_session_local.return_value.close.assert_called_once()

    def test_save_file(self, mock_user, mock_data_files):
        """Test _save_file method."""
        # Setup
        manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
        manager.files = mock_data_files.return_value
        file_details = {"filename": "test.xlsx", "contents": b"file content"}

        # Execute
        result = manager._save_file(file_details, "xlsx")

        # Assert
        assert result == ("/path/to/file", "filename.ext")
        manager.files.save.assert_called_once_with("xlsx", b"file content", "test.xlsx")

    def test_execute_import(self, mock_user):
        """Test execute_import function."""
        # Setup
        with patch("app.imports.import_manager.threading.Thread") as mock_thread:
            manager = ImportManager(mock_user, ImportManager.USDM_EXCEL)
            manager.process = AsyncMock()

            # Execute
            execute_import(manager)

            # Assert
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()
