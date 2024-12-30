from collections import OrderedDict
from datetime import date

class DictResult():

  def __init__(self, item):
    self.result = self._to_dict(dict(item))

  def _to_dict(self, value):
    if isinstance(value, list):
      result = []
      for v in value:
        result.append(self._to_dict(v))
      return result
    elif isinstance(value, dict):
      result = {}
      for k, v in value.items():
        result[k] = self._to_dict(v)
      return result
    elif isinstance(value, str) or isinstance(value, int) or isinstance(value, float) or value is None:
      return value
    elif isinstance(value, date):
      return str(value)
    elif isinstance(value, OrderedDict):
      return self._to_dict(dict(value))
    else:
      #print(f"TYPE: {value}")
      return self._to_dict(value.__dict__)
  