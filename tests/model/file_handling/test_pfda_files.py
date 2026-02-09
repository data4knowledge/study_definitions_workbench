import json
from unittest.mock import patch, MagicMock
from app.model.file_handling.pfda_files import PFDAFiles


class TestPFDAFilesDir:
    @patch("app.model.file_handling.pfda_files.subprocess.run")
    def test_dir_success(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"files": [{"name": "file1.xlsx"}]})
        )
        pf = PFDAFiles()
        success, data, error = pf.dir("/")
        assert success is True
        assert len(data["files"]) == 1

    @patch("app.model.file_handling.pfda_files.subprocess.run")
    def test_dir_error_response(self, mock_run):
        mock_run.return_value = MagicMock(stdout=json.dumps({"error": "not found"}))
        pf = PFDAFiles()
        success, data, error = pf.dir("/")
        assert success is False
        assert error == "not found"

    @patch("app.model.file_handling.pfda_files.subprocess.run")
    def test_dir_exception(self, mock_run):
        mock_run.side_effect = Exception("pfda not installed")
        pf = PFDAFiles()
        success, data, error = pf.dir("/")
        assert success is False
        assert "pfda not installed" in error


class TestPFDAFilesDownload:
    @patch("builtins.open", create=True)
    @patch("app.model.file_handling.pfda_files.subprocess.run")
    def test_download(self, mock_run, mock_open, tmp_path):
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"result": str(tmp_path / "downloaded.xlsx")})
        )
        mock_open.return_value.__enter__ = MagicMock(
            return_value=MagicMock(read=MagicMock(return_value=b"data"))
        )
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        pf = PFDAFiles()
        pf._files = MagicMock()
        pf._files.path.return_value = str(tmp_path)
        stem, ext, contents = pf.download("uid-123")
        assert stem == "downloaded"
        assert ext == "xlsx"
