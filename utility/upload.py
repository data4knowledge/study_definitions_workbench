import os
from fastapi import File
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