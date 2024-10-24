import os
#from pathlib import Path
from d4kms_generic import application_logger
from d4kms_generic.service_environment import ServiceEnvironment

class LocalFiles:
  
  def __init__(self, uuid=None):
    se = ServiceEnvironment()
    self.root = se.get("LOCALFILE_PATH")

  def list(self, dir):
    try:
      root, dirs, files = os.walk(dir)
      return {'files': files, 'dirs': dirs}
    except Exception as e:
      application_logger.exception(f"Exception listing local files dir '{dir}'", e)
      return {'error': f"Exception '{e}' listing local files dir '{dir}'",}

