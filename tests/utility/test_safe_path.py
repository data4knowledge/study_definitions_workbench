import pytest
from fastapi import HTTPException

from app.configuration.configuration import application_configuration
from app.utility.safe_path import safe_data_path, safe_identifier


@pytest.mark.parametrize("v", ["prism3", "StudyDesign_1", "ScheduleTimeline_2", "M11", "1.0.0"])
def test_identifier_ok(v):
    assert safe_identifier(v) == v


@pytest.mark.parametrize("v", ["", "../x", "a/b", "a\\b", "..", "x" * 200, "a b"])
def test_identifier_rejected(v):
    with pytest.raises(HTTPException) as e:
        safe_identifier(v)
    assert e.value.status_code == 404


def test_data_path_inside(tmp_path, monkeypatch):
    monkeypatch.setattr(application_configuration, "data_file_path", str(tmp_path))
    f = tmp_path / "u" / "f.json"
    f.parent.mkdir()
    f.write_text("{}")
    assert safe_data_path(str(f)) == str(f.resolve())


def test_data_path_outside(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(application_configuration, "data_file_path", str(data))
    with pytest.raises(HTTPException):
        safe_data_path(str(tmp_path / "secret.txt"))
    with pytest.raises(HTTPException):
        safe_data_path(str(data / ".." / "secret.txt"))
