import json
from tests.files.files import read_json, write_json, read_excel
from usdm_db import USDMDb
from app.model.file_handling.data_files import DataFiles

SAVE = False


def _run_test(name, save=False):
    filename = f"{name}.xlsx"
    contents = read_excel(_full_path(filename))
    files = DataFiles()
    _ = files.new()
    files.save("xlsx", contents, filename)
    db = USDMDb()
    _ = db.from_excel(_full_path(filename))
    result = db.to_json()
    pretty_result = json.dumps(json.loads(result), indent=2)
    result_filename = filename = f"{name}_usdm.json"
    if save or SAVE:
        write_json(_full_path(result_filename), result)
    expected = read_json(_full_path(result_filename))
    assert pretty_result == expected


def _full_path(filename):
    return f"tests/test_files/excel/{filename}"


def test_excel_pilot():
    _run_test("pilot")
