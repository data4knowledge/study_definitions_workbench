import os
from fastapi import File
from model.files import Files
from model.file_import import FileImport
from d4kms_generic import application_logger

async def get_xl_files(form: File):
  images = []
  messages = []
  excel = None
  files = form.getlist('files')
  for v in files:
    filename = v.filename
    contents = await v.read()
    file_root, file_extension = os.path.splitext(filename)
    if file_extension == '.xlsx':
      messages.append(f"Excel file '{filename}' accepted")
      excel = {'filename': filename, 'contents': contents}
      application_logger.info(f"Processing upload file '{file_root}'")
    elif file_extension in ['.png', 'jpg', 'jpeg']:
      messages.append(f"Image file '{filename}' accepted")
      images.append({'filename': filename, 'contents': contents})
      application_logger.info(f"Processing upload file '{file_root}'")
    else:
      messages.append(f"File '{filename}' was ignored, not .xlsx or an image file")
  return excel, images, messages

def save_xl_files(excel: dict, images: dict, user_id, db):
  filename = excel['filename']
  contents = excel['contents']
  full_path = Files.save(uuid, filename, "xlsx", contents)
  file_import = FileImport.create(fullpath='', filename='', user_id=user_id, db=db)
  uuid = file_import.uuid      
  for image in images:

  self._save_source_file(record['uuid'], contents)
    self._save_images(record['uuid'], images)
    record.update({ 

  def _save_source_file(self, uuid, contents):
    try:
      full_path = self._file_path(uuid, 'definition', 'xlsx')
      with open(full_path, 'wb') as f:
        f.write(contents)
      return full_path
    except Exception as e:
      application_logger.exception(f"Exception saving source file", e)

  def _save_images(self, uuid, images):
    for image in images:
      try:
        full_path = self._image_file_path(uuid, image['filename'])
        with open(full_path, 'wb') as f:
          f.write(image['contents'])
      except Exception as e:
        application_logger.exception(f"Exception saving source file", e)


async def get_m11_files(form: File):
  images = []
  messages = []
  excel = None
  files = form.getlist('files')
  for v in files:
    filename = v.filename
    contents = await v.read()
    file_root, file_extension = os.path.splitext(filename)
    if file_extension == '.docx':
      messages.append(f"Word file '{filename}' accepted")
      excel = {'filename': filename, 'contents': contents}
      application_logger.info(f"Processing upload file '{file_root}'")
    else:
      messages.append(f"File '{filename}' was ignored, not .docx file")
  return excel, [], messages