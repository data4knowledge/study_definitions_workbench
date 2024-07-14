import os
from fastapi import File
from model.files import Files
#from model.file_import import FileImport
from d4kms_generic import application_logger
from utility.background import process_excel

async def process_xl(request, background_tasks, templates):
  try:
    form = await request.form()
    excel, images, messages = await get_xl_files(form)
    if excel:
      file_path, uuid = save_xl_files(excel, images)
      if uuid:
        background_tasks.add_task(process_excel, uuid)
        return templates.TemplateResponse('import/partials/upload_success.html', {"request": request, 'filename': excel['filename'], 'messages': messages})  
      else:
        messages.append("Failed to process the Excel file")
        return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': excel['filename'], 'messages': messages})  
    else:
      messages.append("No Excel file detected, file upload ignored")
      return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': messages})  
  except Exception as e:
    application_logger.exception("Exception uploading files", e)
    return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': ['Exception raised while uploading files, see logs for more information']})  

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
  files = Files()
  filename = excel['filename']
  contents = excel['contents']
  uuid, full_path = files.save(uuid, filename, "xlsx", contents)
  for image in images:
    filename = image['filename']
    contents = image['contents']
    uuid, full_path = files.save(uuid, filename, "image", contents)

async def process_m11(request, background_tasks, templates):
  try:
    form = await request.form()
    word, messages = await get_m11_files(form)
    if word:
      uuid = save_m11_files(word)
      if uuid:
        background_tasks.add_task(process_excel, uuid)
        return templates.TemplateResponse('import/partials/upload_success.html', {"request": request, 'filename': word['filename'], 'messages': messages})  
      else:
        messages.append("Failed to process the Excel file")
        return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': word['filename'], 'messages': messages})  
    else:
      messages.append("No Word file detected, file upload ignored")
      return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': messages})  
  except Exception as e:
    application_logger.exception("Exception uploading files", e)
    return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': ['Exception raised while uploading files, see logs for more information']})  

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
  return excel, messages

def save_m11_files(excel: dict, user_id, db):
  files = Files()
  filename = excel['filename']
  contents = excel['contents']
  uuid, full_path = files.save(uuid, filename, "docx", contents)
  