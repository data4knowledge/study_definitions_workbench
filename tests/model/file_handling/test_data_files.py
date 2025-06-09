import pytest
from unittest.mock import mock_open

from app.model.file_handling.data_files import DataFiles


class TestDataFiles:
    """Tests for the DataFiles class."""

    @pytest.fixture
    def mock_config(self, mocker):
        """Mock application configuration."""
        mock = mocker.patch(
            "app.model.file_handling.data_files.application_configuration"
        )
        mock.data_file_path = "/test/data/path"
        mock.mount_path = "/test/mount/path"
        mock.database_path = "/test/database/path"
        mock.local_file_path = "/test/local/path"
        return mock

    @pytest.fixture
    def mock_logger(self, mocker):
        """Mock application logger."""
        return mocker.patch("app.model.file_handling.data_files.application_logger")

    @pytest.fixture
    def data_files(self, mock_config):
        """Create a DataFiles instance for testing."""
        return DataFiles()

    @pytest.fixture
    def data_files_with_uuid(self, mock_config):
        """Create a DataFiles instance with a predefined UUID."""
        return DataFiles(uuid="test-uuid")

    def test_init_without_uuid(self, data_files, mock_config):
        """Test initialization without a UUID."""
        assert data_files.uuid is None
        assert data_files.dir == "/test/data/path"
        assert len(data_files.media_type) > 0

    def test_init_with_uuid(self, data_files_with_uuid, mock_config):
        """Test initialization with a UUID."""
        assert data_files_with_uuid.uuid == "test-uuid"
        assert data_files_with_uuid.dir == "/test/data/path"

    def test_new_success(self, data_files, mocker):
        """Test creating a new UUID directory successfully."""
        mock_uuid = mocker.patch("app.model.file_handling.data_files.uuid4")
        mock_uuid.return_value = "new-test-uuid"

        mocker.patch.object(data_files, "_create_dir", return_value=True)

        result = data_files.new()

        assert result == "new-test-uuid"
        assert data_files.uuid == "new-test-uuid"
        data_files._create_dir.assert_called_once()

    def test_new_failure(self, data_files, mocker):
        """Test creating a new UUID directory with failure."""
        mock_uuid = mocker.patch("app.model.file_handling.data_files.uuid4")
        mock_uuid.return_value = "new-test-uuid"

        mocker.patch.object(data_files, "_create_dir", return_value=False)

        result = data_files.new()

        assert result is None
        assert data_files.uuid is None
        data_files._create_dir.assert_called_once()

    def test_create_dir_success(self, data_files_with_uuid, mocker):
        """Test _create_dir method success."""
        mock_mkdir = mocker.patch("os.mkdir")

        result = data_files_with_uuid._create_dir()

        assert result is True
        mock_mkdir.assert_called_once_with("/test/data/path/test-uuid")

    def test_create_dir_failure(self, data_files_with_uuid, mocker, mock_logger):
        """Test _create_dir method failure."""
        mock_mkdir = mocker.patch("os.mkdir")
        mock_mkdir.side_effect = Exception("Test error")

        result = data_files_with_uuid._create_dir()

        assert result is False
        mock_mkdir.assert_called_once_with("/test/data/path/test-uuid")
        mock_logger.exception.assert_called_once()

    def test_save_with_original_filename(self, data_files_with_uuid, mocker):
        """Test save method with original filename."""
        # Mock the specific save method
        mock_save_method = mocker.MagicMock(
            return_value="/test/data/path/test-uuid/test.xlsx"
        )

        # Set up the media type to use original filename
        data_files_with_uuid.media_type["xlsx"]["use_original"] = True
        data_files_with_uuid.media_type["xlsx"]["method"] = mock_save_method

        result, filename = data_files_with_uuid.save(
            "xlsx", b"test content", "test.xlsx"
        )

        assert result == "/test/data/path/test-uuid/test.xlsx"
        assert filename == "test.xlsx"
        mock_save_method.assert_called_once_with(b"test content", "test.xlsx")

    def test_save_with_generated_filename(self, data_files_with_uuid, mocker):
        """Test save method with generated filename."""
        # Mock the specific save method
        mock_save_method = mocker.MagicMock(
            return_value="/test/data/path/test-uuid/usdm.json"
        )

        # Set up the media type to use generated filename
        data_files_with_uuid.media_type["usdm"]["use_original"] = False
        data_files_with_uuid.media_type["usdm"]["method"] = mock_save_method

        # Mock the _form_filename method
        mocker.patch.object(
            data_files_with_uuid, "_form_filename", return_value="usdm.json"
        )

        result, filename = data_files_with_uuid.save("usdm", '{"test": "content"}')

        assert result == "/test/data/path/test-uuid/usdm.json"
        assert filename == "usdm.json"
        data_files_with_uuid._form_filename.assert_called_once_with("usdm")
        mock_save_method.assert_called_once_with('{"test": "content"}', "usdm.json")

    def test_read(self, data_files_with_uuid, mocker):
        """Test read method."""
        mock_open_file = mock_open(read_data="test content")
        mocker.patch("builtins.open", mock_open_file)

        # Mock the _form_filename and _file_path methods
        mocker.patch.object(
            data_files_with_uuid, "_form_filename", return_value="test.txt"
        )
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.txt",
        )

        result = data_files_with_uuid.read("test")

        assert result == "test content"
        data_files_with_uuid._form_filename.assert_called_once_with("test")
        data_files_with_uuid._file_path.assert_called_once_with("test.txt")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/test.txt", "r"
        )

    def test_path_with_original_filename(self, data_files_with_uuid, mocker):
        """Test path method with original filename."""
        # Set up the media type to use original filename
        data_files_with_uuid.media_type["xlsx"]["use_original"] = True
        data_files_with_uuid.media_type["xlsx"]["extension"] = "xlsx"

        # Mock the _dir_files_by_extension method
        mocker.patch.object(
            data_files_with_uuid, "_dir_files_by_extension", return_value=["test.xlsx"]
        )

        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.xlsx",
        )

        full_path, filename, exists = data_files_with_uuid.path("xlsx")

        assert full_path == "/test/data/path/test-uuid/test.xlsx"
        assert filename == "test.xlsx"
        assert exists is True
        data_files_with_uuid._dir_files_by_extension.assert_called_once_with("xlsx")
        data_files_with_uuid._file_path.assert_called_once_with("test.xlsx")

    def test_path_with_multiple_files_error(
        self, data_files_with_uuid, mocker, mock_logger
    ):
        """Test path method with multiple files error."""
        # Set up the media type to use original filename
        data_files_with_uuid.media_type["xlsx"]["use_original"] = True
        data_files_with_uuid.media_type["xlsx"]["extension"] = "xlsx"

        # Mock the _dir_files_by_extension method to return multiple files
        mocker.patch.object(
            data_files_with_uuid,
            "_dir_files_by_extension",
            return_value=["test1.xlsx", "test2.xlsx"],
        )

        with pytest.raises(DataFiles.LogicError):
            data_files_with_uuid.path("xlsx")

        data_files_with_uuid._dir_files_by_extension.assert_called_once_with("xlsx")
        mock_logger.error.assert_called_once()

    def test_path_with_generated_filename_exists(self, data_files_with_uuid, mocker):
        """Test path method with generated filename that exists."""
        # Set up the media type to use generated filename
        data_files_with_uuid.media_type["usdm"]["use_original"] = False

        # Mock the _form_filename method
        mocker.patch.object(
            data_files_with_uuid, "_form_filename", return_value="usdm.json"
        )

        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/usdm.json",
        )

        # Mock os.path.exists
        mocker.patch("os.path.exists", return_value=True)

        full_path, filename, exists = data_files_with_uuid.path("usdm")

        assert full_path == "/test/data/path/test-uuid/usdm.json"
        assert filename == "usdm.json"
        assert exists is True
        data_files_with_uuid._form_filename.assert_called_once_with("usdm")
        data_files_with_uuid._file_path.assert_called_once_with("usdm.json")

    def test_path_with_generated_filename_not_exists(
        self, data_files_with_uuid, mocker
    ):
        """Test path method with generated filename that doesn't exist."""
        # Set up the media type to use generated filename
        data_files_with_uuid.media_type["usdm"]["use_original"] = False

        # Mock the _form_filename method
        mocker.patch.object(
            data_files_with_uuid, "_form_filename", return_value="usdm.json"
        )

        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/usdm.json",
        )

        # Mock os.path.exists
        mocker.patch("os.path.exists", return_value=False)

        full_path, filename, exists = data_files_with_uuid.path("usdm")

        assert full_path == "/test/data/path/test-uuid/usdm.json"
        assert filename == "usdm.json"
        assert exists is False
        data_files_with_uuid._form_filename.assert_called_once_with("usdm")
        data_files_with_uuid._file_path.assert_called_once_with("usdm.json")

    def test_generic_path_exists(self, data_files_with_uuid, mocker):
        """Test generic_path method with file that exists."""
        # Mock the _form_filename method
        mocker.patch.object(
            data_files_with_uuid, "_form_filename", return_value="test.txt"
        )

        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.txt",
        )

        # Mock os.path.exists
        mocker.patch("os.path.exists", return_value=True)

        full_path, filename, exists = data_files_with_uuid.generic_path("test")

        assert full_path == "/test/data/path/test-uuid/test.txt"
        assert filename == "test.txt"
        assert exists is True
        data_files_with_uuid._form_filename.assert_called_once_with("test")
        data_files_with_uuid._file_path.assert_called_once_with("test.txt")

    def test_generic_path_not_exists(self, data_files_with_uuid, mocker):
        """Test generic_path method with file that doesn't exist."""
        # Mock the _form_filename method
        mocker.patch.object(
            data_files_with_uuid, "_form_filename", return_value="test.txt"
        )

        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.txt",
        )

        # Mock os.path.exists
        mocker.patch("os.path.exists", return_value=False)

        full_path, filename, exists = data_files_with_uuid.generic_path("test")

        assert full_path == "/test/data/path/test-uuid/test.txt"
        assert filename == "test.txt"
        assert exists is False
        data_files_with_uuid._form_filename.assert_called_once_with("test")
        data_files_with_uuid._file_path.assert_called_once_with("test.txt")

    def test_delete_success(self, data_files_with_uuid, mocker, mock_logger):
        """Test delete method success."""
        # Mock the _dir_path method
        mocker.patch.object(
            data_files_with_uuid, "_dir_path", return_value="/test/data/path/test-uuid"
        )

        # Mock shutil.rmtree
        mock_rmtree = mocker.patch("shutil.rmtree")

        result = data_files_with_uuid.delete()

        assert result is True
        data_files_with_uuid._dir_path.assert_called_once()
        mock_rmtree.assert_called_once_with("/test/data/path/test-uuid")
        mock_logger.info.assert_called_once()

    def test_delete_failure(self, data_files_with_uuid, mocker, mock_logger):
        """Test delete method failure."""
        # Mock the _dir_path method
        mocker.patch.object(
            data_files_with_uuid, "_dir_path", return_value="/test/data/path/test-uuid"
        )

        # Mock shutil.rmtree to raise an exception
        mock_rmtree = mocker.patch("shutil.rmtree")
        mock_rmtree.side_effect = Exception("Test error")

        result = data_files_with_uuid.delete()

        assert result is False
        data_files_with_uuid._dir_path.assert_called_once()
        mock_rmtree.assert_called_once_with("/test/data/path/test-uuid")
        mock_logger.exception.assert_called_once()

    def test_delete_all_success(self, data_files, mocker, mock_logger):
        """Test delete_all method success."""
        # Mock os.walk
        mock_walk = mocker.patch("os.walk")
        mock_walk.return_value = [
            ("/test/data/path", ["dir1", "dir2"], ["file1.txt", "file2.txt"]),
            ("/test/data/path/dir1", [], ["file3.txt"]),
            ("/test/data/path/dir2", [], ["file4.txt"]),
        ]

        # Mock os.unlink and shutil.rmtree
        mock_unlink = mocker.patch("os.unlink")
        mock_rmtree = mocker.patch("shutil.rmtree")

        result = data_files.delete_all()

        assert result is True
        assert mock_unlink.call_count == 4  # 4 files
        assert mock_rmtree.call_count == 2  # 2 directories
        mock_logger.info.assert_called_once()

    def test_delete_all_failure(self, data_files, mocker, mock_logger):
        """Test delete_all method failure."""
        # Mock os.walk to raise an exception
        mock_walk = mocker.patch("os.walk")
        mock_walk.side_effect = Exception("Test error")

        result = data_files.delete_all()

        assert result is False
        mock_logger.exception.assert_called_once()

    def test_clean_and_tidy_success(self, mock_config, mocker, mock_logger):
        """Test clean_and_tidy class method success."""
        # Set up the keep directories
        keep_dirs = [
            "/test/mount/path/data/file/path",
            "/test/mount/path/database/path",
            "/test/mount/path/local/file/path",
        ]

        # Mock os.listdir
        mock_listdir = mocker.patch("os.listdir")
        mock_listdir.return_value = ["file1.txt", "dir1", "dir2", "keep_dir"]

        # Mock os.path.isfile
        mock_isfile = mocker.patch("os.path.isfile")
        mock_isfile.side_effect = [
            True,
            False,
            False,
            False,
        ]  # file1.txt is a file, others are directories

        # Mock os.path.join
        mock_join = mocker.patch("os.path.join")
        mock_join.side_effect = [
            "/test/mount/path/file1.txt",
            "/test/mount/path/file1.txt",
            "/test/mount/path/dir1",
            "/test/mount/path/dir1",
            "/test/mount/path/dir2",
            "/test/mount/path/dir2",
            "/test/mount/path/keep_dir",
            "/test/mount/path/keep_dir",
        ]

        # Mock os.unlink and shutil.rmtree
        mock_unlink = mocker.patch("os.unlink")
        mock_rmtree = mocker.patch("shutil.rmtree")

        # Mock the keep directories check
        mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))

        # Set up the mock_config to return the correct paths
        mock_config.mount_path = "/test/mount/path"
        mock_config.data_file_path = "/test/mount/path/data/file/path"
        mock_config.database_path = "/test/mount/path/database/path"
        mock_config.local_file_path = "/test/mount/path/local/file/path"

        result = DataFiles.clean_and_tidy()

        assert result is True
        mock_unlink.assert_called_once()
        # The clean_and_tidy method logs "Deleted datafiles dir" but doesn't actually delete it
        # So we expect rmtree to be called for dir1, dir2, and keep_dir (if it's not in keep)
        assert mock_rmtree.call_count == 3
        assert mock_logger.info.call_count >= 3

    def test_clean_and_tidy_failure(self, mock_config, mocker, mock_logger):
        """Test clean_and_tidy class method failure."""
        # Mock os.listdir to raise an exception
        mock_listdir = mocker.patch("os.listdir")
        mock_listdir.side_effect = Exception("Test error")

        result = DataFiles.clean_and_tidy()

        assert result is False
        mock_logger.exception.assert_called_once()

    def test_check_success_create_dir(self, mock_config, mocker, mock_logger):
        """Test check class method success when creating directory."""
        # Mock os.mkdir
        mock_mkdir = mocker.patch("os.mkdir")

        result = DataFiles.check()

        assert result is True
        mock_mkdir.assert_called_once_with("/test/data/path")
        mock_logger.info.assert_called()

    def test_check_success_dir_exists(self, mock_config, mocker, mock_logger):
        """Test check class method success when directory already exists."""
        # Mock os.mkdir to raise FileExistsError
        mock_mkdir = mocker.patch("os.mkdir")
        mock_mkdir.side_effect = FileExistsError()

        result = DataFiles.check()

        assert result is None  # The method doesn't return anything in this case
        mock_mkdir.assert_called_once_with("/test/data/path")
        mock_logger.info.assert_called()

    def test_check_failure(self, mock_config, mocker, mock_logger):
        """Test check class method failure."""
        # Mock os.mkdir to raise an exception
        mock_mkdir = mocker.patch("os.mkdir")
        mock_mkdir.side_effect = Exception("Test error")

        result = DataFiles.check()

        assert result is False
        mock_mkdir.assert_called_once_with("/test/data/path")
        mock_logger.exception.assert_called_once()

    def test_save_excel_file(self, data_files_with_uuid, mocker):
        """Test _save_excel_file method."""
        # Mock the _save_binary_file method
        mock_save_binary = mocker.patch.object(
            data_files_with_uuid, "_save_binary_file"
        )
        mock_save_binary.return_value = "/test/data/path/test-uuid/test.xlsx"

        # The _save_excel_file method doesn't return anything, it just calls _save_binary_file
        data_files_with_uuid._save_excel_file(b"test content", "test.xlsx")

        # Verify that _save_binary_file was called with the correct arguments
        mock_save_binary.assert_called_once_with(b"test content", "test.xlsx")

    def test_save_word_file(self, data_files_with_uuid, mocker):
        """Test _save_word_file method."""
        # Mock the _save_binary_file method
        mock_save_binary = mocker.patch.object(
            data_files_with_uuid, "_save_binary_file"
        )
        mock_save_binary.return_value = "/test/data/path/test-uuid/test.docx"

        # The _save_word_file method doesn't return anything, it just calls _save_binary_file
        data_files_with_uuid._save_word_file(b"test content", "test.docx")

        # Verify that _save_binary_file was called with the correct arguments
        mock_save_binary.assert_called_once_with(b"test content", "test.docx")

    def test_save_binary_file(self, data_files_with_uuid, mocker):
        """Test _save_binary_file method."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.bin",
        )

        # Mock open
        mock_open_file = mock_open()
        mocker.patch("builtins.open", mock_open_file)

        result = data_files_with_uuid._save_binary_file(b"test content", "test.bin")

        assert result == "/test/data/path/test-uuid/test.bin"
        data_files_with_uuid._file_path.assert_called_once_with("test.bin")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/test.bin", "wb"
        )
        mock_open_file().write.assert_called_once_with(b"test content")

    def test_save_binary_file_exception(
        self, data_files_with_uuid, mocker, mock_logger
    ):
        """Test _save_binary_file method with exception."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.bin",
        )

        # Mock open to raise an exception
        mock_open_file = mock_open()
        mock_open_file.side_effect = Exception("Test error")
        mocker.patch("builtins.open", mock_open_file)

        result = data_files_with_uuid._save_binary_file(b"test content", "test.bin")

        assert result is None
        data_files_with_uuid._file_path.assert_called_once_with("test.bin")
        mock_logger.exception.assert_called_once()

    def test_save_image_file(self, data_files_with_uuid, mocker):
        """Test _save_image_file method."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/image.png",
        )

        # Mock open
        mock_open_file = mock_open()
        mocker.patch("builtins.open", mock_open_file)

        data_files_with_uuid._save_image_file(b"test content", "image.png")

        data_files_with_uuid._file_path.assert_called_once_with("image.png")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/image.png", "wb"
        )
        mock_open_file().write.assert_called_once_with(b"test content")

    def test_save_json_file(self, data_files_with_uuid, mocker):
        """Test _save_json_file method."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.json",
        )

        # Mock open
        mock_open_file = mock_open()
        mocker.patch("builtins.open", mock_open_file)

        # Mock json.loads and json.dumps
        mock_json_loads = mocker.patch("json.loads")
        mock_json_loads.return_value = {"test": "content"}

        mock_json_dumps = mocker.patch("json.dumps")
        mock_json_dumps.return_value = '{\n  "test": "content"\n}'

        result = data_files_with_uuid._save_json_file(
            '{"test": "content"}', "test.json"
        )

        assert result == "/test/data/path/test-uuid/test.json"
        data_files_with_uuid._file_path.assert_called_once_with("test.json")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/test.json", "w", encoding="utf-8"
        )
        mock_json_loads.assert_called_once_with('{"test": "content"}')
        mock_json_dumps.assert_called_once_with({"test": "content"}, indent=2)
        mock_open_file().write.assert_called_once_with('{\n  "test": "content"\n}')

    def test_save_json_file_exception(self, data_files_with_uuid, mocker, mock_logger):
        """Test _save_json_file method with exception."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.json",
        )

        # Mock json.loads to raise an exception
        mock_json_loads = mocker.patch("json.loads")
        mock_json_loads.side_effect = Exception("Test error")

        result = data_files_with_uuid._save_json_file(
            '{"test": "content"}', "test.json"
        )

        assert result is None
        data_files_with_uuid._file_path.assert_called_once_with("test.json")
        mock_logger.exception.assert_called_once()

    def test_save_yaml_file(self, data_files_with_uuid, mocker):
        """Test _save_yaml_file method."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.yaml",
        )

        # Mock open
        mock_open_file = mock_open()
        mocker.patch("builtins.open", mock_open_file)

        # Mock yaml.dump
        mock_yaml_dump = mocker.patch("yaml.dump")

        result = data_files_with_uuid._save_yaml_file({"test": "content"}, "test.yaml")

        assert result == "/test/data/path/test-uuid/test.yaml"
        data_files_with_uuid._file_path.assert_called_once_with("test.yaml")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/test.yaml", "w"
        )
        mock_yaml_dump.assert_called_once_with(
            {"test": "content"}, mock_open_file(), default_flow_style=False
        )

    def test_save_yaml_file_exception(self, data_files_with_uuid, mocker, mock_logger):
        """Test _save_yaml_file method with exception."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.yaml",
        )

        # Mock open to raise an exception
        mock_open_file = mock_open()
        mock_open_file.side_effect = Exception("Test error")
        mocker.patch("builtins.open", mock_open_file)

        result = data_files_with_uuid._save_yaml_file({"test": "content"}, "test.yaml")

        assert result is None
        data_files_with_uuid._file_path.assert_called_once_with("test.yaml")
        mock_logger.exception.assert_called_once()

    def test_save_pdf_file(self, data_files_with_uuid, mocker):
        """Test _save_pdf_file method."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.pdf",
        )

        # Mock open
        mock_open_file = mock_open()
        mocker.patch("builtins.open", mock_open_file)

        result = data_files_with_uuid._save_pdf_file(b"test content", "test.pdf")

        assert result == "/test/data/path/test-uuid/test.pdf"
        data_files_with_uuid._file_path.assert_called_once_with("test.pdf")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/test.pdf", "w+b"
        )
        mock_open_file().write.assert_called_once_with(b"test content")

    def test_save_pdf_file_exception(self, data_files_with_uuid, mocker, mock_logger):
        """Test _save_pdf_file method with exception."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.pdf",
        )

        # Mock open to raise an exception
        mock_open_file = mock_open()
        mock_open_file.side_effect = Exception("Test error")
        mocker.patch("builtins.open", mock_open_file)

        result = data_files_with_uuid._save_pdf_file(b"test content", "test.pdf")

        assert result is None
        data_files_with_uuid._file_path.assert_called_once_with("test.pdf")
        mock_logger.exception.assert_called_once()

    def test_save_html_file(self, data_files_with_uuid, mocker):
        """Test _save_html_file method."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.html",
        )

        # Mock open
        mock_open_file = mock_open()
        mocker.patch("builtins.open", mock_open_file)

        result = data_files_with_uuid._save_html_file("<html>test</html>", "test.html")

        assert result == "/test/data/path/test-uuid/test.html"
        data_files_with_uuid._file_path.assert_called_once_with("test.html")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/test.html", "w", encoding="utf-8"
        )
        mock_open_file().write.assert_called_once_with("<html>test</html>")

    def test_save_html_file_exception(self, data_files_with_uuid, mocker, mock_logger):
        """Test _save_html_file method with exception."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.html",
        )

        # Mock open to raise an exception
        mock_open_file = mock_open()
        mock_open_file.side_effect = Exception("Test error")
        mocker.patch("builtins.open", mock_open_file)

        result = data_files_with_uuid._save_html_file("<html>test</html>", "test.html")

        assert result is None
        data_files_with_uuid._file_path.assert_called_once_with("test.html")
        mock_logger.exception.assert_called_once()

    def test_save_csv_file(self, data_files_with_uuid, mocker):
        """Test _save_csv_file method."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.csv",
        )

        # Mock open
        mock_open_file = mock_open()
        mocker.patch("builtins.open", mock_open_file)

        # Mock csv.DictWriter
        mock_dict_writer = mocker.MagicMock()
        mock_csv_dict_writer = mocker.patch("csv.DictWriter")
        mock_csv_dict_writer.return_value = mock_dict_writer

        contents = [{"col1": "val1", "col2": "val2"}]

        result = data_files_with_uuid._save_csv_file(contents, "test.csv")

        assert result == "/test/data/path/test-uuid/test.csv"
        data_files_with_uuid._file_path.assert_called_once_with("test.csv")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/test.csv", "w", newline=""
        )
        mock_csv_dict_writer.assert_called_once_with(
            mock_open_file(), fieldnames=["col1", "col2"]
        )
        mock_dict_writer.writeheader.assert_called_once()
        mock_dict_writer.writerows.assert_called_once_with(contents)

    def test_save_csv_file_empty_contents(self, data_files_with_uuid, mocker):
        """Test _save_csv_file method with empty contents."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.csv",
        )

        # Mock open
        mock_open_file = mock_open()
        mocker.patch("builtins.open", mock_open_file)

        # Mock csv.DictWriter
        mock_dict_writer = mocker.MagicMock()
        mock_csv_dict_writer = mocker.patch("csv.DictWriter")
        mock_csv_dict_writer.return_value = mock_dict_writer

        result = data_files_with_uuid._save_csv_file(None, "test.csv")

        assert result == "/test/data/path/test-uuid/test.csv"
        data_files_with_uuid._file_path.assert_called_once_with("test.csv")
        mock_open_file.assert_called_once_with(
            "/test/data/path/test-uuid/test.csv", "w", newline=""
        )
        mock_csv_dict_writer.assert_called_once_with(
            mock_open_file(), fieldnames=["message"]
        )
        mock_dict_writer.writeheader.assert_called_once()
        mock_dict_writer.writerows.assert_called_once_with([{"message": "No errors"}])

    def test_save_csv_file_exception(self, data_files_with_uuid, mocker, mock_logger):
        """Test _save_csv_file method with exception."""
        # Mock the _file_path method
        mocker.patch.object(
            data_files_with_uuid,
            "_file_path",
            return_value="/test/data/path/test-uuid/test.csv",
        )

        # Mock open to raise an exception
        mock_open_file = mock_open()
        mock_open_file.side_effect = Exception("Test error")
        mocker.patch("builtins.open", mock_open_file)

        contents = [{"col1": "val1", "col2": "val2"}]

        result = data_files_with_uuid._save_csv_file(contents, "test.csv")

        assert result is None
        data_files_with_uuid._file_path.assert_called_once_with("test.csv")
        mock_logger.exception.assert_called_once()

    def test_dir_path(self, data_files_with_uuid):
        """Test _dir_path method."""
        result = data_files_with_uuid._dir_path()

        assert result == "/test/data/path/test-uuid"

    def test_file_path(self, data_files_with_uuid):
        """Test _file_path method."""
        result = data_files_with_uuid._file_path("test.txt")

        assert result == "/test/data/path/test-uuid/test.txt"

    def test_form_filename(self, data_files_with_uuid):
        """Test _form_filename method."""
        # Set up the media type
        data_files_with_uuid.media_type["test"] = {
            "filename": "test",
            "extension": "txt",
        }

        result = data_files_with_uuid._form_filename("test")

        assert result == "test.txt"

    def test_dir_files_by_extension(self, data_files_with_uuid, mocker):
        """Test _dir_files_by_extension method."""
        # Mock the _dir_files method
        mocker.patch.object(
            data_files_with_uuid,
            "_dir_files",
            return_value=["file1.txt", "file2.txt", "file3.csv"],
        )

        # Mock the _extension method
        mocker.patch.object(
            data_files_with_uuid, "_extension", side_effect=lambda f: f.split(".")[-1]
        )

        result = data_files_with_uuid._dir_files_by_extension("txt")

        assert result == ["file1.txt", "file2.txt"]
        data_files_with_uuid._dir_files.assert_called_once()
        assert data_files_with_uuid._extension.call_count == 3

    def test_dir_files(self, data_files_with_uuid, mocker):
        """Test _dir_files method."""
        # Mock the _dir_path method
        mocker.patch.object(
            data_files_with_uuid, "_dir_path", return_value="/test/data/path/test-uuid"
        )

        # Mock os.listdir
        mocker.patch("os.listdir", return_value=["file1.txt", "file2.txt", "subdir"])

        # Mock os.path.isfile
        mocker.patch("os.path.isfile", side_effect=lambda p: not p.endswith("subdir"))

        # Mock os.path.join
        mocker.patch("os.path.join", side_effect=lambda *args: "/".join(args))

        result = data_files_with_uuid._dir_files()

        assert result == ["file1.txt", "file2.txt"]
        data_files_with_uuid._dir_path.assert_called_once()

    def test_stem_and_extension(self, data_files_with_uuid):
        """Test _stem_and_extension method."""
        result = data_files_with_uuid._stem_and_extension("test.txt")

        assert result == ("test", "txt")

    def test_extension(self, data_files_with_uuid):
        """Test _extension method."""
        result = data_files_with_uuid._extension("test.txt")

        assert result == "txt"
