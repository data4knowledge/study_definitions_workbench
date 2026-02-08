import os
from unittest.mock import patch, MagicMock
from app.model.file_handling.local_files import LocalFiles


class TestLocalFilesCheck:

    @patch("app.model.file_handling.local_files.os.mkdir")
    def test_creates_dir(self, mock_mkdir):
        mock_mkdir.return_value = None
        result = LocalFiles.check()
        assert result is True
        mock_mkdir.assert_called_once()

    @patch("app.model.file_handling.local_files.os.mkdir")
    def test_dir_exists(self, mock_mkdir):
        mock_mkdir.side_effect = FileExistsError()
        result = LocalFiles.check()
        assert result is None  # returns None (no explicit return on FileExistsError)

    @patch("app.model.file_handling.local_files.os.mkdir")
    def test_exception(self, mock_mkdir):
        mock_mkdir.side_effect = Exception("fail")
        result = LocalFiles.check()
        assert result is False


class TestLocalFilesDir:

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_dir_with_files(self, mock_config, tmp_path):
        mock_config.local_file_path = str(tmp_path)
        # Create test files and dirs
        (tmp_path / "file1.txt").write_text("hello")
        (tmp_path / "file2.xlsx").write_text("data")
        (tmp_path / "subdir").mkdir()
        lf = LocalFiles()
        success, data, error = lf.dir(str(tmp_path))
        assert success is True
        assert len(data["files"]) > 0
        names = [f["name"] for f in data["files"]]
        assert "file1.txt" in names
        assert "file2.xlsx" in names
        assert "subdir" in names

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_dir_at_root(self, mock_config, tmp_path):
        root = str(tmp_path)
        mock_config.local_file_path = root
        lf = LocalFiles()
        (tmp_path / "file.txt").write_text("hi")
        success, data, error = lf.dir(root)
        assert success is True
        # At root, should not have ".." entry
        names = [f["name"] for f in data["files"]]
        assert ".." not in names

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_hidden_files_excluded(self, mock_config, tmp_path):
        mock_config.local_file_path = str(tmp_path)
        (tmp_path / ".hidden").write_text("secret")
        (tmp_path / "~$lockfile.xlsx").write_text("lock")
        (tmp_path / "visible.txt").write_text("ok")
        lf = LocalFiles()
        success, data, error = lf.dir(str(tmp_path))
        assert success is True
        names = [f["name"] for f in data["files"]]
        assert ".hidden" not in names
        assert "~$lockfile.xlsx" not in names
        assert "visible.txt" in names

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_dir_subdirectory(self, mock_config, tmp_path):
        root = str(tmp_path)
        mock_config.local_file_path = root
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("hi")
        lf = LocalFiles()
        success, data, error = lf.dir(str(subdir))
        assert success is True
        names = [f["name"] for f in data["files"]]
        assert ".." in names

    @patch("app.model.file_handling.local_files.application_configuration")
    @patch("app.model.file_handling.local_files.os.scandir")
    def test_exception(self, mock_scandir, mock_config):
        mock_config.local_file_path = "/fake"
        mock_scandir.side_effect = Exception("scandir fail")
        lf = LocalFiles()
        success, data, error = lf.dir("/fake")
        assert success is False
        assert "scandir fail" in error


class TestLocalFilesDownload:

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_download(self, mock_config, tmp_path):
        mock_config.local_file_path = str(tmp_path)
        test_file = tmp_path / "testfile.xlsx"
        test_file.write_bytes(b"file contents")
        lf = LocalFiles()
        stem, ext, contents = lf.download(str(test_file))
        assert stem == "testfile"
        assert ext == "xlsx"
        assert contents == b"file contents"


class TestSizeToString:

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_zero(self, mock_config):
        mock_config.local_file_path = "/fake"
        lf = LocalFiles()
        assert lf._size_to_string(0) == "0B"

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_bytes(self, mock_config):
        mock_config.local_file_path = "/fake"
        lf = LocalFiles()
        assert "B" in lf._size_to_string(500)

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_kb(self, mock_config):
        mock_config.local_file_path = "/fake"
        lf = LocalFiles()
        assert "KB" in lf._size_to_string(2048)

    @patch("app.model.file_handling.local_files.application_configuration")
    def test_mb(self, mock_config):
        mock_config.local_file_path = "/fake"
        lf = LocalFiles()
        assert "MB" in lf._size_to_string(2 * 1024 * 1024)
