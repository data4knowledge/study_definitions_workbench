import json
import subprocess
from d4kms_generic.logger import application_logger
from app.model.file_handling.pfda.pfda_files import PFDAFiles

class PFDA():

  def __init__(self):
    self._files = PFDAFiles()

  def dir(self, dir):
    try:
      args = ["pfda", "ls", '-json']
      result = subprocess.run(args, capture_output=True, text=True)
      response = json.loads(result.stdout)
      if 'error' in response:
        application_logger.error(f"pFDA error: {response['error']}")
        return False, {}, response['error']
      else:
        application_logger.info(f"pFDA file list response: {response}")
        return True, {'files': response['files'], 'source': 'pfda'}, ''
    except Exception as e:
      application_logger.exception(f"pFDA exception", e)
      return False, {}, f"Exception '{e}' raised, check the logs for more information"

  def download(self, uid: str):
    target = self._files.path()
    args = ["pfda", "download", uid, f'-output', f'{target}', '-json', '-overwrite', 'true']
    #print(f"ARGS: {args}")
    result = subprocess.run(args, capture_output=True, text=True)
    #print(f"RESULT: {result}")
    application_logger.info(f"PFDA download: {result.stdout}")
    files = json.loads(result.stdout)
    file_root, file_extension, contents = self._files.read(files['result'])
    return file_root, file_extension, contents

