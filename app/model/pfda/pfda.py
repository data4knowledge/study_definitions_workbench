import json
import subprocess
from d4kms_generic.logger import application_logger
from app.model.pfda.pfda_files import PFDAFiles

class PFDA():

  def __init__(self):
    self._files = PFDAFiles()

  def dir(self, dir):
    args = ["pfda", "ls", '-json']
    result = subprocess.run(args, capture_output=True, text=True)
    application_logger.info(f"PFDA file list: {result.stdout}")
    listing = json.loads(result.stdout)
    return listing['files']

  def download(self, uid: str):
    target = self._files.path()
    args = ["pfda", "download", uid, f'-output', f'{target}', '-json', '-overwrite', 'true']
    print(f"ARGS: {args}")
    result = subprocess.run(args, capture_output=True, text=True)
    print(f"RESULT: {result}")
    application_logger.info(f"PFDA download: {result.stdout}")
    files = json.loads(result.stdout)
    file_root, file_extension, contents = self._files.read(files['result'])
    return file_root, file_extension, contents

