import os
import json
import csv
import shutil
from pathlib import Path
from uuid import uuid4
from d4kms_generic import application_logger

class Files:
  
  DIR = "datafiles"

  def __init__(self, uuid=None):
    self.media_type = {
      "xlsx": {'method': self._save_excel_file, 'use_original':  False, 'filename': 'xl'},
      "docx": {'method': self._save_word_file, 'use_original':  False, 'filename': 'doc'},
      "usdm": {'method': self._save_json_file, 'use_original':  False, 'filename': 'usdm'},
      "fhir": {'method': self._save_json_file, 'use_original':  False, 'filename': 'fhir'},
      "errors": {'method': self._save_csv_file, 'use_original':  False, 'filename': 'errors'},
      "protocol": {'method': self._save_html_file, 'use_original':  False, 'filename': 'protocol'},
      "highlight": {'method': self._save_html_file, 'use_original':  False, 'filename': 'highlight'},
      "image": {'method': self._save_image_file, 'use_original':  True, 'filename': ''}
    }
    self.uuid = uuid

  def new(self):
    self.uuid = str(uuid4())
    if not self._create_dir(self.uuid):
      self.uuid = None
    return self.uuid

  def save(self, filename, type, contents):
    filename = filename if self.media_type[type]['use_original'] else self.media_type[type]['filename']
    full_path = self.media_type[type]['method'](self.uuid, contents, filename)
    return full_path 

  def read(self, uuid, type):
    full_path = self._file_path(uuid, self.media_type[type]['filename'], type)
    with open(full_path, "r") as stream:
      return stream.read()

  def path(self, uuid, type):
    return self._file_path(uuid, self.media_type[type]['filename'], type)

  def delete(self, uuid):
    try:
      path = self._dir_path(uuid)
      shutil.rmtree(path) 
      return True
    except Exception as e:
      application_logger.exception(f"Exception deleting directory '{path}'", e)
      return False
  
  def _save_excel_file(self, uuid, contents, suffix):
    self._save_binary_file(uuid, contents, suffix, 'xlsx')

  def _save_word_file(self, uuid, contents, suffix):
    self._save_binary_file(uuid, contents, suffix, 'docx')

  def _save_binary_file(self, uuid, contents, suffix, extension):
    try:
      full_path = self._file_path(uuid, suffix, extension)
      with open(full_path, 'wb') as f:
        f.write(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving source file", e)

  def _save_image_file(self, uuid, contents, filename):
    try:
      stem, ext = self._stem_and_extension(filename)
      print(f"STEM, EXT: {stem}, {ext}")
      full_path = self._file_path(uuid, stem, ext)
      with open(full_path, 'wb') as f:
        f.write(contents)
    except Exception as e:
      application_logger.exception(f"Exception saving source file", e)

  def _save_json_file(self, uuid, contents, filename):
    try:
      full_path = self._file_path(uuid, filename, 'json')
      with open(full_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(json.loads(contents), indent=2))
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving results file", e)

  def _save_pdf_file(self, uuid, contents, filename):
    try:
      full_path = self._file_path(uuid, filename, 'pdf')
      with open(full_path, 'w+b') as f:
        f.write(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving PDF file", e)

  def _save_html_file(self, uuid, contents, filename):
    try:
      full_path = self._file_path(uuid, filename, 'html')
      with open(full_path, 'w', encoding='utf-8') as f:
        f.write(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving timeline file", e)

  def _save_csv_file(self, uuid, contents, filename):
    if not contents:
      contents = [{'sheet': '', 'row': '', 'column': '', 'message': '', 'level': ''}]
    try:
      full_path = self._file_path(uuid, filename, 'csv')
      with open(full_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(contents[0].keys()))
        writer.writeheader()
        writer.writerows(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving error file", e)

  def _create_dir(self, uuid):
    try:
      os.mkdir(os.path.join(self.DIR, uuid))
      return True
    except Exception as e:
      application_logger.exception(f"Exception creating dir '{uuid}'", e)
      return False

  def _file_path(self, uuid, filename, extension):
    return os.path.join(self.DIR, uuid, f"{filename}.{extension}")

  def _dir_path(self, uuid):
    return os.path.join(self.DIR, uuid)

  def _stem_and_extension(self, filename):
    path_filename = Path(filename)
    return path_filename.stem, path_filename.suffix[1:]
