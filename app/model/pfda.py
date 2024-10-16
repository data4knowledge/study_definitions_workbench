import json
import subprocess
from d4kms_generic.logger import application_logger

class PFDA():

  def dir(self, dir):
    result = subprocess.run(["pfda", "ls", '-json'], capture_output=True, text=True)
    listing = json.loads(result.stdout)
    application_logger.info(f"PFDA file list: {listing['files']}")
    return listing['files']
