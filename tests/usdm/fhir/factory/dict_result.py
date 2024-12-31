import json
from collections import OrderedDict
from datetime import date

class DictResult():

  def __init__(self, item):
    self.dict = json.loads(item.json())
    self.pretty = json.dumps(self.dict, indent=2)
    self.result = self.dict