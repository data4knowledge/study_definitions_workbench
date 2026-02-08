from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from app.utility.soup import get_soup


class TestGetSoup:

    def test_basic_html(self):
        result = get_soup("<p>Hello</p>")
        assert isinstance(result, BeautifulSoup)
        assert result.text == "Hello"

    def test_empty_string(self):
        result = get_soup("")
        assert isinstance(result, BeautifulSoup)

    @patch("app.utility.soup.application_logger")
    @patch("app.utility.soup.BeautifulSoup", side_effect=Exception("parse error"))
    def test_exception_returns_empty(self, mock_bs, mock_logger):
        result = get_soup("<broken>")
        assert result == ""
        mock_logger.exception.assert_called_once()

    @patch("app.utility.soup.application_logger")
    def test_warning_logged(self, mock_logger):
        import warnings
        with patch("app.utility.soup.warnings.catch_warnings") as mock_cw:
            warning_item = MagicMock()
            warning_item.message = "test warning"
            mock_cw.return_value.__enter__ = MagicMock(return_value=[warning_item])
            mock_cw.return_value.__exit__ = MagicMock(return_value=False)
            result = get_soup("<p>test</p>")
            mock_logger.warning.assert_called_once()
