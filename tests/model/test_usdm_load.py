from unittest.mock import MagicMock

import pytest

from app.model.exceptions import USDMLoadException
from app.model.usdm_load import load_usdm4, validation_problems


def _bad_data():
    # Not a full study: enough for pydantic to report a non-UUID study.id.
    return {"study": {"id": "5ce2159ef12f1f3c", "name": "x"}}


class TestLoadUSDM4:
    def test_returns_wrapper(self):
        usdm4 = MagicMock()
        wrapper = load_usdm4(usdm4, {"study": {}})
        assert wrapper is usdm4.loadd.return_value

    def test_raises_when_load_fails(self):
        usdm4 = MagicMock()
        usdm4.loadd.return_value = None
        with pytest.raises(USDMLoadException) as info:
            load_usdm4(usdm4, _bad_data())
        assert any(p.startswith("study.id: ") for p in info.value.problems)


class TestValidationProblems:
    def test_names_field_and_reason(self):
        problems = validation_problems(_bad_data())
        study_id = [p for p in problems if p.startswith("study.id: ")]
        assert len(study_id) == 1
        assert "UUID" in study_id[0]

    def test_non_dict_input(self):
        problems = validation_problems(None)
        assert len(problems) >= 1

    def test_valid_data_fallback_message(self, monkeypatch):
        monkeypatch.setattr(
            "app.model.usdm_load.Wrapper.model_validate", lambda data: None
        )
        assert validation_problems({}) == ["The file could not be loaded as USDM v4"]
