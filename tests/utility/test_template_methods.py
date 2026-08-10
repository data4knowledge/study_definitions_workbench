import json
from unittest.mock import MagicMock, patch
from app.utility.template_methods import (
    server_name,
    single_multiple,
    restructure_study_list,
    convert_to_json,
)


class TestServerName:
    def _make_request(self, url):
        request = MagicMock()
        request.base_url = url
        return request

    def test_staging(self):
        assert (
            server_name(self._make_request("https://staging.example.com")) == "STAGING"
        )

    def test_training(self):
        assert (
            server_name(self._make_request("https://training.example.com"))
            == "TRAINING"
        )

    def test_production(self):
        assert (
            server_name(self._make_request("https://d4k-sdw.example.com"))
            == "PRODUCTION"
        )

    def test_development_localhost(self):
        assert server_name(self._make_request("http://localhost:8000")) == "DEVELOPMENT"

    def test_development_000(self):
        assert server_name(self._make_request("http://0.0.0.0:8000")) == "DEVELOPMENT"

    def test_prism(self):
        assert server_name(self._make_request("https://app.dnanexus.cloud")) == "PRISM"

    def test_unknown(self):
        result = server_name(self._make_request("https://other.example.com"))
        assert result == "https://other.example.com"


class TestSingleMultiple:
    @patch("app.utility.template_methods.application_configuration")
    def test_single(self, mock_config):
        mock_config.single_user = True
        assert single_multiple() == "SINGLE"

    @patch("app.utility.template_methods.application_configuration")
    def test_multiple(self, mock_config):
        mock_config.single_user = False
        assert single_multiple() == "MULTIPLE"


class TestRestructureStudyList:
    def test_basic(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = restructure_study_list(data)
        assert result == {"a": (1, 3), "b": (2, 4)}

    def test_empty(self):
        assert restructure_study_list([]) == {}

    def test_with_all_dicts(self):
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 5, "b": 6}]
        result = restructure_study_list(data)
        assert result == {"a": (1, 3, 5), "b": (2, 4, 6)}

    def test_all_none(self):
        assert restructure_study_list([None, None]) == {}


class TestConvertToJson:
    def test_basic(self):
        data = {"key": "value"}
        result = convert_to_json(data)
        assert json.loads(result) == data

class TestEllipsize:
    def test_short_text_unchanged(self):
        from app.utility.template_methods import ellipsize

        assert ellipsize("Design One") == "Design One"

    def test_exact_length_unchanged(self):
        from app.utility.template_methods import ellipsize

        assert ellipsize("x" * 30) == "x" * 30

    def test_long_text_truncated(self):
        from app.utility.template_methods import ellipsize

        result = ellipsize("USDM Example Study Design With A Long Name")
        assert len(result) == 30
        assert result.endswith("…")

    def test_custom_length(self):
        from app.utility.template_methods import ellipsize

        assert ellipsize("abcdefghij", 5) == "abcd…"

    def test_trailing_space_stripped(self):
        from app.utility.template_methods import ellipsize

        # char before the cut is a space: no "word …" gap
        assert ellipsize("abcd efghij", 6) == "abcd…"

    def test_none_is_empty(self):
        from app.utility.template_methods import ellipsize

        assert ellipsize(None) == ""
