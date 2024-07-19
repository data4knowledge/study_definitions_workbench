import re
from d4kms_generic import application_logger

class ObjectPath():

  def __init__(self, top_level: object) -> None:
    self._top_level = top_level
    self._queue = None
    self._original_path = None

  def get(self, path: str) -> str:
    self._original_path = path
    path = path[1:] if path.startswith('/') else path
    path = path[:-1] if path.endswith('/') else path
    self._queue = path.split('/')
    return self._path(self._top_level, self._pop())

  def _path(self, object_value: object, instruction: str) -> object:
    try:
      group_result = re.match(r"(?P<attribute>\w+)(@(?P<name>\w+)='(?P<value>\w+)')?(\[(?P<subpath>\S+)\])?(\[(?P<index>\d+)\])?", instruction)
      result = group_result.groupdict()
      if result['name'] and result['value'] and result['attribute']:
        object_value = getattr(object_value, result['attribute'], None)
        if isinstance(object_value, dict):
          for key, item in object_value:
            if getattr(item, result['name'], None) == result['value']:
              object_value = item
              break
        else:
          for item in object_value:
            if getattr(item, result['name'], None) == result['value']:
              object_value = item
              break
      elif result['subpath'] and result['attribute']:
        print(f"SUBPATH: {result['subpath']}")
      elif result['index'] and result['attribute']:
        object_value = getattr(object_value, result['attribute'], None)[int(result['index'])]
      elif result['attribute']:
        object_value = getattr(object_value, result['attribute'], None)
      else:
        application_logger.error(f"Failed to find path '{self._original_path}'")
        object_value = None
      return object_value if self._empty() or None else self._path(object_value, self._pop())
    except Exception as e:
      application_logger.exception(f"Exception raised processing object path '{self._original_path}'", e)

  def _pop(self):
    return self._queue.pop(0)

  def _empty(self):
    return len(self._queue) == 0