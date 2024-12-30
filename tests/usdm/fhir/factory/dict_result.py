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
    elif isinstance(value, str) or value is None:
      return value
    else:
      return self._to_dict(dict(value))
  