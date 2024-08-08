import os
from fastapi import File
from app.model.files import Files
#from app.model.file_import import FileImport
from d4kms_generic import application_logger
from app.utility.background import process_excel, process_word

async def process_xl(request, background_tasks, templates, user, session):
  try:
    form = await request.form()
    excel_file, image_files, messages = await get_xl_files(form)
    if excel_file:
      uuid = save_xl_files(excel_file, image_files)
      if uuid:
        background_tasks.add_task(process_excel, uuid, user, session)
        return templates.TemplateResponse('import/partials/upload_success.html', {"request": request, 'filename': excel_file['filename'], 'messages': messages})  
      else:
        messages.append("Failed to process the Excel file")
        return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': excel_file['filename'], 'messages': messages})  
    else:
      messages.append("No Excel file detected, file upload ignored")
      return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': messages})  
  except Exception as e:
    application_logger.exception("Exception uploading files", e)
    return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': ['Exception raised while uploading files, see logs for more information']})  

async def get_xl_files(form: File):
  image_files = []
  messages = []
  excel_file = None
  files = form.getlist('files')
  for v in files:
    filename = v.filename
    contents = await v.read()
    file_root, file_extension = os.path.splitext(filename)
    if file_extension == '.xlsx':
      messages.append(f"Excel file '{filename}' accepted")
      excel_file = {'filename': filename, 'contents': contents}
      application_logger.info(f"Processing upload file '{file_root}'")
    elif file_extension in ['.png', 'jpg', 'jpeg']:
      messages.append(f"Image file '{filename}' accepted")
      image_files.append({'filename': filename, 'contents': contents})
      application_logger.info(f"Processing upload file '{file_root}'")
    else:
      messages.append(f"File '{filename}' was ignored, not .xlsx or an image file")
  return excel_file, image_files, messages

def save_xl_files(excel_file: dict, image_files: dict):
  files = Files()
  uuid = files.new()
  filename = excel_file['filename']
  contents = excel_file['contents']
  saved_full_path, saved_filename = files.save("xlsx", contents, filename)
  for image in image_files:
    filename = image['filename']
    contents = image['contents']
    saved_full_path, saved_filename = files.save("image", contents, filename)
  return uuid

async def process_m11(request, background_tasks, templates, user, session):
  try:
    form = await request.form()
    word_file, messages = await get_m11_files(form)
    if word_file:
      uuid = save_m11_files(word_file)
      if uuid:
        background_tasks.add_task(process_word, uuid, user, session)
        return templates.TemplateResponse('import/partials/upload_success.html', {"request": request, 'filename': word_file['filename'], 'messages': messages})  
      else:
        messages.append("Failed to process the Excel file")
        return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': word_file['filename'], 'messages': messages})  
    else:
      messages.append("No Word file detected, file upload ignored")
      return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': messages})  
  except Exception as e:
    application_logger.exception("Exception uploading files", e)
    return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': ['Exception raised while uploading files, see logs for more information']})  

async def get_m11_files(form: File):
  messages = []
  word_file = None
  files = form.getlist('files')
  for v in files:
    filename = v.filename
    contents = await v.read()
    file_root, file_extension = os.path.splitext(filename)
    if file_extension == '.docx':
      messages.append(f"Word file '{filename}' accepted")
      word_file = {'filename': filename, 'contents': contents}
      application_logger.info(f"Processing upload file '{file_root}'")
    else:
      messages.append(f"File '{filename}' was ignored, not .docx file")
  return word_file, messages

def save_m11_files(word_file: dict):
  files = Files()
  uuid = files.new()
  filename = word_file['filename']
  contents = word_file['contents']
  saved_full_path, saved_filename = files.save("docx", contents, filename)
  return uuid