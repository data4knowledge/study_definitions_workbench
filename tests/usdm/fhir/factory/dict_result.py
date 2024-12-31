import os
import json
from tests.files. files import *

class DictResult():

  def __init__(self, item):
    self.dict = json.loads(item.json())
    self.pretty = json.dumps(self.dict, indent=2)
    self.result = self.dict

  def results_match_file(self, path: str, filename: str, save_file: bool=False):
    if save_file:
      write_json(self._full_path(path, filename), self.pretty)
    expected = read_json(self._full_path(path, filename))
    return self.pretty == expected

  def _full_path(self, path: str, filename: str) -> str:
    return os.path.join(path, filename)
