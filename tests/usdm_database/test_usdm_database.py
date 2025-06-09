import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.usdm_database.usdm_database import USDMDatabase
from app.database.version import Version
from app.database.file_import import FileImport
from app.model.file_handling.data_files import DataFiles


class TestUSDMDatabase:
    """Tests for the USDMDatabase class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def mock_version(self):
        """Create a mock Version object."""
        version = MagicMock(spec=Version)
        version.import_id = 123
        return version

    @pytest.fixture
    def mock_file_import(self):
        """Create a mock FileImport object."""
        file_import = MagicMock(spec=FileImport)
        file_import.uuid = "test-uuid"
        file_import.type = "test-type"
        return file_import

    @pytest.fixture
    def mock_data_files(self):
        """Create a mock DataFiles object."""
        data_files = MagicMock(spec=DataFiles)
        data_files.path.return_value = ("/path/to/usdm.json", "usdm.json", True)
        data_files.generic_path.return_value = (
            "/path/to/excel.xlsx",
            "excel.xlsx",
            False,
        )
        return data_files

    def test_init(self, mocker, mock_session, mock_version, mock_file_import):
        """Test initialization of USDMDatabase."""
        # Mock Version.find and FileImport.find
        mocker.patch("app.database.version.Version.find", return_value=mock_version)
        mocker.patch(
            "app.database.file_import.FileImport.find", return_value=mock_file_import
        )

        # Mock DataFiles constructor
        mock_data_files_init = mocker.patch(
            "app.model.file_handling.data_files.DataFiles.__init__", return_value=None
        )

        # Create USDMDatabase instance
        usdm_db = USDMDatabase(1, mock_session)

        # Verify the initialization
        assert usdm_db.id == 1
        assert usdm_db.uuid == "test-uuid"
        assert usdm_db.type == "test-type"

        # Verify the mocks were called correctly
        Version.find.assert_called_once_with(1, mock_session)
        FileImport.find.assert_called_once_with(123, mock_session)
        mock_data_files_init.assert_called_once_with("test-uuid")

    def test_excel(
        self, mocker, mock_session, mock_version, mock_file_import, mock_data_files
    ):
        """Test the excel method."""
        # Mock Version.find and FileImport.find
        mocker.patch("app.database.version.Version.find", return_value=mock_version)
        mocker.patch(
            "app.database.file_import.FileImport.find", return_value=mock_file_import
        )

        # Mock DataFiles constructor and instance
        mocker.patch(
            "app.model.file_handling.data_files.DataFiles.__init__", return_value=None
        )
        mocker.patch(
            "app.model.file_handling.data_files.DataFiles.path",
            return_value=("/path/to/usdm.json", "usdm.json", True),
        )
        mocker.patch(
            "app.model.file_handling.data_files.DataFiles.generic_path",
            return_value=("/path/to/excel.xlsx", "excel.xlsx", False),
        )

        # Mock USDM4Excel
        mock_usdm4excel = MagicMock()
        mock_usdm4excel_class = mocker.patch(
            "app.usdm_database.usdm_database.USDM4Excel", return_value=mock_usdm4excel
        )

        # Create USDMDatabase instance
        usdm_db = USDMDatabase(1, mock_session)

        # Call the excel method
        result = usdm_db.excel()

        # Verify the result
        assert result == (
            "/path/to/excel.xlsx",
            "excel.xlsx",
            "application/vnd.ms-excel",
        )

        # Verify the mocks were called correctly
        mock_usdm4excel_class.assert_called_once()
        mock_usdm4excel.to_excel.assert_called_once_with(
            "/path/to/usdm.json", "/path/to/excel.xlsx"
        )

    def test_excel_with_exception(
        self, mocker, mock_session, mock_version, mock_file_import
    ):
        """Test the excel method when an exception occurs."""
        # Mock Version.find and FileImport.find
        mocker.patch("app.database.version.Version.find", return_value=mock_version)
        mocker.patch(
            "app.database.file_import.FileImport.find", return_value=mock_file_import
        )

        # Mock DataFiles constructor and instance
        mocker.patch(
            "app.model.file_handling.data_files.DataFiles.__init__", return_value=None
        )
        mocker.patch(
            "app.model.file_handling.data_files.DataFiles.path",
            return_value=("/path/to/usdm.json", "usdm.json", True),
        )
        mocker.patch(
            "app.model.file_handling.data_files.DataFiles.generic_path",
            return_value=("/path/to/excel.xlsx", "excel.xlsx", False),
        )

        # Mock USDM4Excel to raise an exception
        mock_usdm4excel = MagicMock()
        mock_usdm4excel.to_excel.side_effect = Exception("Test error")
        mocker.patch(
            "app.usdm_database.usdm_database.USDM4Excel", return_value=mock_usdm4excel
        )

        # Create USDMDatabase instance
        usdm_db = USDMDatabase(1, mock_session)

        # Call the excel method and expect an exception
        with pytest.raises(Exception) as excinfo:
            usdm_db.excel()

        # Verify the exception
        assert "Test error" in str(excinfo.value)

        # Verify the mocks were called correctly
        mock_usdm4excel.to_excel.assert_called_once_with(
            "/path/to/usdm.json", "/path/to/excel.xlsx"
        )
