import json
from tests.files.files import read_json, write_json, read_excel
from usdm4_excel import USDM4Excel
from app.model.file_handling.data_files import DataFiles

SAVE = False


def _run_test(name, save=False):
    filename = f"{name}.xlsx"
    contents = read_excel(_full_path(filename))
    files = DataFiles()
    _ = files.new()
    files.save("xlsx", contents, filename)
    ue = USDM4Excel()
    wrapper = ue.from_excel(_full_path(filename))
    assert wrapper is not None, ue.errors().dump()
    result = wrapper.to_json()
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


def test_excel_pilot_multi():
    """Multi-design format: a main workbook whose 'studyDesigns' row
    references one external workbook per design. ``from_excel`` on the
    main workbook resolves the design workbook from the same directory."""
    ue = USDM4Excel()
    wrapper = ue.from_excel(_full_path("multi/pilot_multi.xlsx"))
    assert wrapper is not None, ue.errors().dump()
    result = wrapper.to_json()
    pretty_result = json.dumps(json.loads(result), indent=2)
    if SAVE:
        write_json(_full_path("multi/pilot_multi_usdm.json"), result)
    expected = read_json(_full_path("multi/pilot_multi_usdm.json"))
    assert pretty_result == expected
    assert len(wrapper.study.versions[0].studyDesigns) == 1
