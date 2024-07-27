import os
import json
import csv
import shutil
from pathlib import Path
from uuid import uuid4
from d4kms_generic import application_logger

class Files:
  
  class LogicError(Exception):
    pass

  DIR = "datafiles"

  def __init__(self, uuid=None):
    self.media_type = {
      "xlsx": {'method': self._save_excel_file, 'use_original': True, 'filename': 'xl', 'extension': 'xlsx'},
      "docx": {'method': self._save_word_file, 'use_original': True, 'filename': 'doc', 'extension': 'docx'},
      "usdm": {'method': self._save_json_file, 'use_original': False, 'filename': 'usdm', 'extension': 'json'},
      "fhir": {'method': self._save_json_file, 'use_original': False, 'filename': 'fhir', 'extension': 'json'},
      "errors": {'method': self._save_csv_file, 'use_original': False, 'filename': 'errors', 'extension': 'csv'},
      "protocol": {'method': self._save_html_file, 'use_original': False, 'filename': 'protocol', 'extension': 'html'},
      "highlight": {'method': self._save_html_file, 'use_original': False, 'filename': 'highlight', 'extension': 'html'},
      "image": {'method': self._save_image_file, 'use_original': True, 'filename': '', 'extension': ''}
    }
    self.uuid = uuid

  def new(self):
    self.uuid = str(uuid4())
    if not self._create_dir(self.uuid):
      self.uuid = None
    return self.uuid

  def save(self, type, contents, filename=''):
    filename = filename if self.media_type[type]['use_original'] else self._form_filename(type)
    full_path = self.media_type[type]['method'](self.uuid, contents, filename)
    return full_path 

  def read(self, type):
    extension = self.media_type[type]['extension']
    full_path = self._file_path(self.uuid, self.media_type[type]['filename'], extension)
    with open(full_path, "r") as stream:
      return stream.read()

  def path(self, type):
    if self.media_type[type]['use_original']:
      files = self._dir_files_by_extension(self.media_type[type]['extension'])
      if len(files) == 1:
        filename = files[0]
      else:
        application_logger.error(f"Found multiple files for type '{type}' when forming path")
        raise self.LogicError
    else:
      filename = self._form_filename(type)
    return self._file_path(filename), filename

  def delete(self):
    try:
      path = self._dir_path()
      shutil.rmtree(path) 
      return True
    except Exception as e:
      application_logger.exception(f"Exception deleting directory '{path}'", e)
      return False
  
  def _save_excel_file(self, uuid, contents, filename):
      self._save_binary_file(uuid, contents, filename)

  def _save_word_file(self, uuid, contents, filename):
      self._save_binary_file(uuid, contents, filename)

  def _save_binary_file(self, uuid, contents, filename):
    try:
      full_path = self._file_path(filename)
      with open(full_path, 'wb') as f:
        f.write(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving source file", e)

  def _save_image_file(self, uuid, contents, filename):
    try:
      full_path = self._file_path(filename)
      with open(full_path, 'wb') as f:
        f.write(contents)
    except Exception as e:
      application_logger.exception(f"Exception saving source file", e)

  def _save_json_file(self, uuid, contents, filename):
    try:
      full_path = self._file_path(filename)
      with open(full_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(json.loads(contents), indent=2))
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving results file", e)

  def _save_pdf_file(self, uuid, contents, filename):
    try:
      full_path = self._file_path(filename)
      with open(full_path, 'w+b') as f:
        f.write(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving PDF file", e)

  def _save_html_file(self, uuid, contents, filename):
    try:
      full_path = self._file_path(filename)
      with open(full_path, 'w', encoding='utf-8') as f:
        f.write(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving timeline file", e)

  def _save_csv_file(self, uuid, contents, filename):
    if not contents:
      contents = [{'sheet': '', 'row': '', 'column': '', 'message': '', 'level': ''}]
    try:
      full_path = self._file_path(filename)
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

  def _dir_path(self):
    return os.path.join(self.DIR, self.uuid)

  def _file_path(self, filename):
    return os.path.join(self.DIR, self.uuid, filename)

  def _form_filename(self, type):
    return f"{self.media_type[type]['filename']}.{self.media_type[type]['extension']}"

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
