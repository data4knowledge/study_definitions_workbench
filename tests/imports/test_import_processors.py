import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from app.imports.import_processors import (
    ImportProcessorBase,
    ImportExcel,
    ImportWord,
    ImportFhirV1,
    ImportUSDM3,
    ImportUSDM4,
)


@pytest.fixture
def mock_usdm_db():
    """Mock the USDMDb class."""
    with patch("app.imports.import_processors.USDMDb") as mock:
        instance = mock.return_value
        instance.from_excel.return_value = None
        instance.from_json.return_value = None
        instance.to_json.return_value = '{"study": {"name": "test-study"}}'
        instance.wrapper.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_m11_protocol():
    """Mock the M11Protocol class."""
    with patch("app.imports.import_processors.M11Protocol") as mock:
        instance = mock.return_value
        instance.process = AsyncMock()
        instance.to_usdm.return_value = '{"study": {"name": "test-study"}}'
        instance.extra.return_value = {
            "title_page": {},
            "amendment": {},
            "miscellaneous": {},
        }
        yield mock


@pytest.fixture
def mock_from_fhir_v1():
    """Mock the FromFHIRV1 class."""
    with patch("app.imports.import_processors.FromFHIRV1") as mock:
        instance = mock.return_value
        instance.to_usdm = AsyncMock(return_value='{"study": {"name": "test-study"}}')
        yield mock


@pytest.fixture
def mock_usdm3():
    """Mock the USDM3 class."""
    with patch("app.imports.import_processors.USDM3") as mock:
        instance = mock.return_value
        instance.convert.return_value = MagicMock()
        instance.convert.return_value.to_json.return_value = (
            '{"study": {"name": "test-study"}}'
        )
        instance.validate.return_value = MagicMock()
        instance.validate.return_value.to_dict.return_value = {"errors": []}
        yield mock


@pytest.fixture
def mock_usdm4():
    """Mock the USDM4 class."""
    with patch("app.imports.import_processors.USDM4") as mock:
        instance = mock.return_value
        instance.convert.return_value = MagicMock()
        instance.convert.return_value.to_json.return_value = (
            '{"study": {"name": "test-study"}}'
        )
        instance.validate.return_value = MagicMock()
        instance.validate.return_value.to_dict.return_value = {"errors": []}
        yield mock


@pytest.fixture
def mock_object_path():
    """Mock the ObjectPath class."""
    with patch("app.imports.import_processors.ObjectPath") as mock:
        instance = mock.return_value
        instance.get.side_effect = lambda path: {
            "study/name": "test-study",
            "study/versions[0]/studyPhase/standardCode/decode": "Phase 1",
        }.get(path, "")
        yield mock


@pytest.fixture
def mock_data_files():
    """Mock the DataFiles class."""
    with patch("app.imports.import_processors.DataFiles") as mock:
        instance = mock.return_value
        instance.path.return_value = ("/path/to/file", "filename.ext", True)
        instance.save.return_value = ("/path/to/file", "filename.ext")
        instance.read.return_value = '{"study": {"name": "test-study"}}'
        yield mock


@pytest.fixture
def mock_logger():
    """Mock the application_logger."""
    with patch("app.imports.import_processors.application_logger") as mock:
        yield mock


class TestImportProcessorBase:
    """Tests for the ImportProcessorBase class."""

    def test_init(self):
        """Test initialization of ImportProcessorBase."""
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        assert processor.usdm is None
        assert processor.errors is None
        assert processor.type == "TEST_TYPE"
        assert processor.uuid == "test-uuid"
        assert processor.full_path == "/path/to/file"
        assert processor.extra == processor._blank_extra()

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process method."""
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        result = await processor.process()
        assert result is None

    def test_blank_extra(self):
        """Test _blank_extra method."""
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        extra = processor._blank_extra()
        assert "amendment" in extra
        assert "miscellaneous" in extra
        assert "title_page" in extra

    def test_study_parameters(self, mock_usdm4, mock_object_path):
        """Test _study_parameters method."""
        # Setup
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        processor.usdm = '{"study": {"name": "test-study"}, "usdmVersion": "1.0"}'

        # Mock the USDMDb wrapper
        db_instance = mock_usdm4.return_value
        wrapper = db_instance.wrapper.return_value
        study = wrapper.study.return_value
        version = study.first_version.return_value
        version.official_title_text.return_value = "Test Study Title"
        version.sponsor_identifier_text.return_value = "TEST-123"
        version.nct_identifier.return_value = "NCT12345678"
        version.sponsor_name.return_value = "Test Sponsor"

        # Execute
        result = processor._study_parameters()
        print(f"RESULT: {result}")

        # Assert
        assert result["name"] == "test-study-TEST_TYPE"
        assert result["phase"] == "Phase 1"
        assert result["full_title"] == "Test Study Title"
        assert result["sponsor_identifier"] == "TEST-123"
        assert result["nct_identifier"] == "NCT12345678"
        assert result["sponsor"] == "Test Sponsor"

        # Verify method calls
        mock_usdm_db.assert_called_once()
        db_instance.from_json.assert_called_once()
        # wrapper is called twice in the implementation
        assert db_instance.wrapper.call_count == 2
        mock_object_path.assert_called_once_with(wrapper)

    def test_study_parameters_exception(self, mock_usdm_db, mock_logger):
        """Test _study_parameters method with exception."""
        # Setup
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        processor.usdm = '{"study": {"name": "test-study"}}'
        mock_usdm_db.return_value.from_json.side_effect = Exception("Test exception")

        # Execute
        result = processor._study_parameters()

        # Assert
        assert result is None
        mock_logger.exception.assert_called_once()

    def test_get_parameter(self, mock_object_path):
        """Test _get_parameter method."""
        # Setup
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")

        # Execute
        result = processor._get_parameter(mock_object_path.return_value, "study/name")

        # Assert
        assert result == "test-study"
        mock_object_path.return_value.get.assert_called_once_with("study/name")

    def test_get_parameter_not_found(self, mock_object_path):
        """Test _get_parameter method with not found path."""
        # Setup
        processor = ImportProcessorBase("TEST_TYPE", "test-uuid", "/path/to/file")
        mock_object_path.return_value.get.return_value = None

        # Execute
        result = processor._get_parameter(
            mock_object_path.return_value, "not/found/path"
        )

        # Assert
        assert result == ""
        mock_object_path.return_value.get.assert_called_once_with("not/found/path")


class TestImportExcel:
    """Tests for the ImportExcel class."""

    @pytest.mark.asyncio
    async def test_process(self, mock_usdm_db):
        """Test process method."""
        # Setup
        processor = ImportExcel("USDM_EXCEL", "test-uuid", "/path/to/file")
        processor.file_import = MagicMock()
        processor.session = MagicMock()

        # Execute
        result = await processor.process()

        # Assert
        assert result == True
        # USDMDb is called multiple times: once in process() and again in _study_parameters()
        assert mock_usdm_db.call_count >= 1
        mock_usdm_db.return_value.from_excel.assert_called_once_with("/path/to/file")
        mock_usdm_db.return_value.to_json.assert_called_once()
        assert processor.usdm == mock_usdm_db.return_value.to_json.return_value
        assert processor.errors == mock_usdm_db.return_value.from_excel.return_value


class TestImportWord:
    """Tests for the ImportWord class."""

    @pytest.mark.asyncio
    async def test_process(self, mock_m11_protocol):
        """Test process method."""
        # Setup
        processor = ImportWord("M11_DOCX", "test-uuid", "/path/to/file")

        # Execute
        result = await processor.process()

        # Assert
        assert result == True
        mock_m11_protocol.assert_called_once()
        mock_m11_protocol.return_value.process.assert_called_once()
        mock_m11_protocol.return_value.to_usdm.assert_called_once()
        mock_m11_protocol.return_value.extra.assert_called_once()
        assert processor.usdm == mock_m11_protocol.return_value.to_usdm.return_value
        assert processor.extra == mock_m11_protocol.return_value.extra.return_value


class TestImportFhirV1:
    """Tests for the ImportFhirV1 class."""

    @pytest.mark.asyncio
    async def test_process(self, mock_from_fhir_v1):
        """Test process method."""
        # Setup
        processor = ImportFhirV1("FHIR_V1_JSON", "test-uuid", "/path/to/file")

        # Execute
        result = await processor.process()

        # Assert
        assert result == True
        mock_from_fhir_v1.assert_called_once_with("test-uuid")
        mock_from_fhir_v1.return_value.to_usdm.assert_called_once()
        # The to_usdm method is mocked to return a string directly, not a coroutine
        assert processor.usdm == mock_from_fhir_v1.return_value.to_usdm.return_value


class TestImportUSDM3:
    """Tests for the ImportUSDM3 class."""

    @pytest.mark.asyncio
    async def test_process(self, mock_data_files, mock_usdm3, mock_usdm4):
        """Test process method."""
        # Setup
        processor = ImportUSDM3("USDM3_JSON", "test-uuid", "/path/to/file")

        # Execute
        result = await processor.process()

        # Assert
        assert result == True
        mock_data_files.assert_called_once_with("test-uuid")
        mock_data_files.return_value.path.assert_called_with("usdm")
        mock_usdm3.assert_called_once()
        mock_usdm3.return_value.validate.assert_called_once_with("/path/to/file")
        mock_usdm4.assert_called_once()
        mock_usdm4.return_value.convert.assert_called_once_with("/path/to/file")
        mock_usdm4.return_value.validate.assert_called_once_with("/path/to/file")
        # Use assert_any_call instead of assert_called_with to check that the method was called with these parameters
        # regardless of the order
        mock_data_files.return_value.save.assert_any_call("usdm", processor.usdm)
        assert (
            processor.usdm
            == mock_usdm3.return_value.convert.return_value.to_json.return_value
        )
        assert (
            processor.errors
            == mock_usdm3.return_value.validate.return_value.to_dict.return_value
        )
        assert processor.success == True
        assert processor.fatal_error == None

    @pytest.mark.asyncio
    async def test_process_error(self, mock_data_files, mock_usdm3):
        """Test process method."""
        instance = mock_usdm3.return_value
        instance.validate.return_value.passed_or_not_implemented = lambda: False
        instance.validate.return_value.to_dict.return_value = {
            "errors": [{"status": "Failure"}]
        }

        # Setup
        processor = ImportUSDM3("USDM3_JSON", "test-uuid", "/path/to/file")

        # Execute with patch to avoid file not found error
        with patch("usdm4.USDM4.convert") as mock_convert:
            result = await processor.process()

        # Assert
        assert result == False
        mock_data_files.assert_called_once_with("test-uuid")
        mock_usdm3.assert_called_once()
        mock_usdm3.return_value.validate.assert_called_once_with("/path/to/file")
        assert processor.success == False
        assert (
            processor.fatal_error
            == "USDM v3 validation failed. Check the file using the validate functionality"
        )


class TestImportUSDM:
    """Tests for the ImportUSDM class."""

    @pytest.mark.asyncio
    async def test_process(self, mock_data_files, mock_usdm4):
        """Test process method."""
        # Setup
        processor = ImportUSDM4("USDM4_JSON", "test-uuid", "/path/to/file")

        # Execute
        result = await processor.process()

        # Assert
        assert result == True
        mock_data_files.assert_called_once_with("test-uuid")
        mock_data_files.return_value.path.assert_called_with("usdm")
        mock_data_files.return_value.read.assert_called_once_with("usdm")
        mock_usdm4.assert_called_once()
        mock_usdm4.return_value.validate.assert_called_once_with("/path/to/file")
        assert processor.usdm == mock_data_files.return_value.read.return_value
        assert (
            processor.errors
            == mock_usdm4.return_value.validate.return_value.to_dict.return_value
        )

    @pytest.mark.asyncio
    async def test_process_error(self, mock_data_files, mock_usdm4):
        """Test process method."""
        instance = mock_usdm4.return_value
        instance.validate.return_value.passed_or_not_implemented = lambda: False
        instance.validate.return_value.to_dict.return_value = {
            "errors": [{"status": "Failure"}]
        }

        # Setup
        processor = ImportUSDM4("USDM4_JSON", "test-uuid", "/path/to/file")

        # Execute
        result = await processor.process()

        # Assert
        assert result == False
        mock_data_files.assert_called_once_with("test-uuid")
        mock_usdm4.assert_called_once()
        mock_usdm4.return_value.validate.assert_called_once_with("/path/to/file")
        assert processor.success == False
        assert (
            processor.fatal_error
            == "USDM v4 validation failed. Check the file using the validate functionality"
        )
