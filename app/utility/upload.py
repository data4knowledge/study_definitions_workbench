import os
import json
from fastapi import File
from starlette.datastructures import FormData
from app.model.files import Files
from app.model.pfda.pfda import PFDA
from d4kms_generic import application_logger
from app.utility.background import process_excel, process_word, process_fhir_v1, run_background_task

async def process_xl(request, templates, user):
  try:
    form = await request.form()
    import_file, image_files, messages = await get_xl_files(form)
    if import_file:
      uuid = save_xl_files(import_file, image_files)
      if uuid:
        #background_tasks.add_task(process_excel, uuid, user, session)
        run_background_task(process_excel, uuid, user)
        return templates.TemplateResponse('import/partials/upload_success.html', {"request": request, 'filename': import_file['filename'], 'messages': messages})  
      else:
        messages.append("Failed to process the Excel file")
        return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': import_file['filename'], 'messages': messages, 'type': 'Excel'})  
    else:
      messages.append("No Excel file detected, file upload ignored")
      return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': messages, 'type': 'Excel'})  
  except Exception as e:
    application_logger.exception("Exception uploading files", e)
    return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': ['Exception raised while uploading files, see logs for more information'], 'type': 'Excel'})  

async def get_xl_files(form: File):
  image_files = []
  messages = []
  import_file = None
  files = form.getlist('files')
  for v in files:
    filename = v.filename
    contents = await v.read()
    file_root, file_extension = os.path.splitext(filename)
    if file_extension == '.xlsx':
      messages.append(f"Excel file '{filename}' accepted")
      import_file = {'filename': filename, 'contents': contents}
      application_logger.info(f"Processing upload file '{file_root}'")
    elif file_extension in ['.png', 'jpg', 'jpeg']:
      messages.append(f"Image file '{filename}' accepted")
      image_files.append({'filename': filename, 'contents': contents})
      application_logger.info(f"Processing upload file '{file_root}'")
    else:
      messages.append(f"File '{filename}' was ignored, not .xlsx or an image file")
  return import_file, image_files, messages

def save_xl_files(import_file: dict, image_files: dict):
  files = Files()
  uuid = files.new()
  saved_full_path, saved_filename = _save_file(files, import_file, "xlsx")
  for image_file in image_files:
    saved_full_path, saved_filename = _save_file(files, image_file, "image")
  return uuid

async def process_m11(request, templates, user, source='os'):
  try:
    form = await request.form()
    print(f"FORM: {type(form)}")
    import_file, messages = await get_m11_files(form) if source == 'os' else await get_m11_files_pfda(form)
    if import_file:
      uuid = save_m11_files(import_file)
      if uuid:
        run_background_task(process_word, uuid, user)
        return templates.TemplateResponse('import/partials/upload_success.html', {"request": request, 'filename': import_file['filename'], 'messages': messages})  
      else:
        messages.append("Failed to process the Word file")
        return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': import_file['filename'], 'messages': messages, 'type': 'Word'})  
    else:
      messages.append("No Word file detected, file upload ignored")
      return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': messages, 'type': 'Word'})  
  except Exception as e:
    application_logger.exception("Exception uploading files", e)
    return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': ['Exception raised while uploading files, see logs for more information'], 'type': 'Word'})  

async def get_m11_files(form: FormData):
  messages = []
  import_file = None
  files = form.getlist('files')
  for v in files:
    filename = v.filename
    contents = await v.read()
    file_root, file_extension = os.path.splitext(filename)
    if file_extension == '.docx':
      messages.append(f"Word file '{filename}' accepted")
      import_file = {'filename': filename, 'contents': contents}
      application_logger.info(f"Processing upload file '{file_root}'")
    else:
      messages.append(f"File '{filename}' was ignored, not .docx file")
  return import_file, messages

async def get_m11_files_pfda(form: FormData):
  messages = []
  import_file = None
  print(f"ITEMS: {form.items()}")
  print(f"ITEMS: {form.getlist('file_list_input')}")
  #print(f"FILES: {json.loads(form[1])}")
  data = form.getlist('file_list_input')
  for uid in json.loads(data[0]):
    print(f"FILE: {uid}")
    pfda = PFDA()
    file_root, file_extension, contents = pfda.download(uid)
    filename = f"{file_root}{file_extension}"
    if file_extension == '.docx':
      messages.append(f"Word file '{filename}' accepted")
      import_file = {'filename': filename, 'contents': contents}
      application_logger.info(f"Processing upload file '{file_root}'")
    else:
      messages.append(f"File '{filename}' was ignored, not .docx file")
  return import_file, messages

def save_m11_files(import_file: dict):
  return _save_files(import_file, "docx")

async def process_fhir(request, templates, user):
  try:
    form = await request.form()
    import_file, messages = await get_fhir_files(form)
    if import_file:
      uuid = save_fhir_files(import_file)
      if uuid:
        #background_tasks.add_task(process_fhir_v1, uuid, user, session)
        run_background_task(process_fhir_v1, uuid, user)
        return templates.TemplateResponse('import/partials/upload_success.html', {"request": request, 'filename': import_file['filename'], 'messages': messages})  
      else:
        messages.append("Failed to process the Excel file")
        return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': import_file['filename'], 'messages': messages, 'type': 'JSON'})  
    else:
      messages.append("No Word file detected, file upload ignored")
      return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': messages, 'type': 'JSON'})  
  except Exception as e:
    application_logger.exception("Exception uploading files", e)
    return templates.TemplateResponse('import/partials/upload_fail.html', {"request": request, 'filename': '', 'messages': ['Exception raised while uploading files, see logs for more information'], 'type': 'JSON'})  

async def get_fhir_files(form: File):
  messages = []
  import_file = None
  files = form.getlist('files')
  for v in files:
    filename = v.filename
    contents = await v.read()
    file_root, file_extension = os.path.splitext(filename)
    if file_extension == '.json':
      messages.append(f"FHIR file '{filename}' accepted")
      import_file = {'filename': filename, 'contents': contents}
      application_logger.info(f"Processing upload file '{file_root}'")
    else:
      messages.append(f"File '{filename}' was ignored, not .json file")
  return import_file, messages

def save_fhir_files(import_file: dict):
  return _save_files(import_file, "fhir")

def _save_files(import_file: dict, type: str) -> str:
  files = Files()
  uuid = files.new()
  saved_full_path, saved_filename = _save_file(files, import_file, type)
  return uuid

def _save_file(files: Files, import_file: dict, type: str) -> tuple[str, str]:
  filename = import_file['filename']
  contents = import_file['contents']
  return files.save(type, contents, filename)
  