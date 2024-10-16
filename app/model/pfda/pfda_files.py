import os
import json
import shutil
from d4kms_generic import application_logger
from d4kms_generic.service_environment import ServiceEnvironment

class PFDAFiles:

  DOWNLOAD_DIR = "pfda_downloads"

  class LogicError(Exception):
    pass

  def __init__(self):
    se = ServiceEnvironment()
    self.dir = se.get("DATAFILE_PATH")
    self._create_dir()

  # def save(self, contents, filename: str) -> tuple[str, str]:
  #   full_path = self._save_binary_file(contents, filename)
  #   return full_path, filename 

  def read(self, full_path):
    print(f"FULL_PATH: {full_path}")
    head_tail = os.path.split(full_path)
    stem, extension = self._stem_and_extension(head_tail[1])
    with open(full_path, "rb") as stream:
      return stem, extension, stream.read()

  def path(self):
    return self._dir_path()
  
  def delete(self):
    path = self._dir_path()
    try:
      shutil.rmtree(path) 
      application_logger.info("Deleted study dir '{path}'")
      return True
    except Exception as e:
      application_logger.exception(f"Exception deleting study dir '{path}'", e)
      return False
  
  def _save_binary_file(self, contents, filename):
    try:
      full_path = self._file_path(filename)
      with open(full_path, 'wb') as f:
        f.write(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving source file", e)

  def _create_dir(self):
    try:
      os.mkdir(os.path.join(self.dir, self.DOWNLOAD_DIR))
      return True
    except FileExistsError as e:
      pass # Expected error
    except Exception as e:
      application_logger.exception(f"Exception creating dir '{self.DOWNLOAD_DIR}' in '{self.dir}'", e)
      return False

  def _dir_path(self):
    return os.path.join(self.dir, self.DOWNLOAD_DIR)

  def _file_path(self, filename):
    return os.path.join(self.dir, self.DOWNLOAD_DIR, filename)

  def _dir_files_by_extension(self, extension):
    dir = self._dir_files()
    return [f for f in dir if self._extension(f) == extension]

  def _dir_files(self):
    path = self._dir_path()
    return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

  def _stem_and_extension(self, filename):
    result = os.path.splitext(filename)
    return result[0], result[1][1:]

  def _extension(self, filename):
    result = os.path.splitext(filename)
    return result[1][1:]
