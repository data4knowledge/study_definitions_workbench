import os
#from pathlib import Path
from d4kms_generic import application_logger
from d4kms_generic.service_environment import ServiceEnvironment

class LocalFiles:
  
  def __init__(self, uuid=None):
    se = ServiceEnvironment()
    self.root = se.get("LOCALFILE_PATH")

  def dir(self, path):
    try:
      result = []
      for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
          result.append({'type': 'File', 'name': item, 'created_at': '', 'file_size': ''})
        else:
          result.append({'type': 'Folder', 'name': item, 'created_at': '', 'file_size': ''})
      return True, result, ''
    except Exception as e:
      application_logger.exception(f"Exception listing local files dir '{dir}'", e)
      return False, {}, f"Exception '{e}' listing local files dir '{dir}'"
