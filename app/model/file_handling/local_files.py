import os
import datetime
import math
from pathlib import Path
from d4kms_generic import application_logger
from d4kms_generic.service_environment import ServiceEnvironment

class LocalFiles:
  
  def __init__(self, uuid=None):
    se = ServiceEnvironment()
    self.root = se.get("LOCALFILE_PATH")

  @classmethod
  def check(cls):
    se = ServiceEnvironment()
    dir = se.get("LOCALFILE_PATH")
    application_logger.info("Checking localfiles dir exists")
    try:
      os.mkdir(dir)
      application_logger.info("Localfiles dir created")
      return True
    except FileExistsError as e:
      application_logger.info("Localfiles dir exists")
    except Exception as e:
      application_logger.exception(f"Exception checking/creating localfiles dir '{dir}'", e)
      return False
    
  def dir(self, path):
    try:
      files = []
      dirs = []
      parts = path.split(self.root)
      rel_dir = parts[-1] if parts[-1] else '/'
      #print(f"DIR: p='{path}', r='{self.root}' e={parts[-1]}")
      if not str(path).endswith(self.root):
        path_obj = Path(path)
        parent_dir = str(path_obj.parent.absolute())
        dirs.append({'uid': parent_dir, 'type': 'Folder', 'name': '..', 'path': str(parent_dir), 'created_at': '', 'file_size': ''})
      for item in os.scandir(path):
        ts = datetime.datetime.fromtimestamp(item.stat().st_atime).isoformat(sep=' ', timespec="seconds")
        size = self._size_to_string(item.stat().st_size)
        if os.path.isfile(item.path):
          start_strings = ['.', '~$']
          if not any(item.name.startswith(x) for x in start_strings):
          #if not item.name.startswith('.'):
            files.append({'uid': item.path, 'type': 'File', 'name': item.name, 'path': item.path, 'created_at': ts, 'file_size': size})
        else:
          dirs.append({'uid': item.path, 'type': 'Folder', 'name': item.name, 'path': item.path, 'created_at': ts, 'file_size': ''})
      results = sorted(dirs, key=lambda d: d['name']) + sorted(files, key=lambda d: d['name'])
      return True, {'files': results, 'dir': rel_dir}, ''
    except Exception as e:
      application_logger.exception(f"Exception listing local files dir '{path}'", e)
      return False, {}, f"Exception '{e}' listing local files dir '{path}'"

  def download(self, path: str):
    application_logger.info(f"Local file download: {path}")
    file_root, file_extension, contents = self._read(path)
    return file_root, file_extension, contents

  def _size_to_string(self, bytes):
    if bytes == 0: 
      return "0B" 
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB") 
    i = int(math.floor(math.log(bytes, 1024)))
    power = math.pow(1024, i) 
    size = round(bytes / power, 2) 
    return "{} {}".format(size, size_name[i])

  def _read(self, full_path):
    #print(f"FULL_PATH: {full_path}")
    head_tail = os.path.split(full_path)
    stem, extension = self._stem_and_extension(head_tail[1])
    with open(full_path, "rb") as stream:
      return stem, extension, stream.read()

  def _stem_and_extension(self, filename):
    result = os.path.splitext(filename)
    return result[0], result[1][1:]