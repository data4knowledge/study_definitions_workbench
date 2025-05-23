import os
import json
from tests.files.files import read_json, write_json
from tests.helpers.helpers import fix_uuid


class DictResult:
    def __init__(self, item):
        raw_json = item.json()
        raw_json = fix_uuid(raw_json)
        self.dict = json.loads(raw_json)
        self.result = self.dict
        self.actual = json.dumps(self.dict, indent=2)
        self.expected = None

    def read_expected(self, path: str, filename: str, save_file: bool = False):
        if save_file:
            write_json(self._full_path(path, filename), self.actual)
        self.expected = read_json(self._full_path(path, filename))

    def _full_path(self, path: str, filename: str) -> str:
        return os.path.join(path, filename)
