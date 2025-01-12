import os
import json
from fastapi import File
from starlette.datastructures import FormData
from app.model.file_handling.data_files import DataFiles
from app.model.file_handling.pfda_files import PFDAFiles
from app.model.file_handling.local_files import LocalFiles
from d4kms_generic import application_logger
from app.utility.background import (
    process_excel,
    process_word,
    process_fhir_v1,
    run_background_task,
)


async def process_xl(request, templates, user, source="browser"):
    files_method = {"browser": get_xl_files, "pfda": None, "os": get_xl_files_os}
    # print(f"PROCESS XL")
    try:
        form = await request.form()
        import_file, image_files, messages = await files_method[source](form)
        if import_file:
            uuid = save_xl_files(import_file, image_files)
            if uuid:
                run_background_task(process_excel, uuid, user)
                return templates.TemplateResponse(
                    "import/partials/upload_success.html",
                    {
                        "request": request,
                        "filename": import_file["filename"],
                        "messages": messages,
                    },
                )
            else:
                messages.append("Failed to process the Excel file")
                return templates.TemplateResponse(
                    "import/partials/upload_fail.html",
                    {
                        "request": request,
                        "filename": import_file["filename"],
                        "messages": messages,
                        "type": "Excel",
                    },
                )
        else:
            messages.append("No Excel file detected, file upload ignored")
            return templates.TemplateResponse(
                "import/partials/upload_fail.html",
                {
                    "request": request,
                    "filename": "",
                    "messages": messages,
                    "type": "Excel",
                },
            )
    except Exception as e:
        application_logger.exception("Exception uploading files", e)
        return templates.TemplateResponse(
            "import/partials/upload_fail.html",
            {
                "request": request,
                "filename": "",
                "messages": [
                    "Exception raised while uploading files, see logs for more information"
                ],
                "type": "Excel",
            },
        )


async def get_xl_files(form: File):
    # print(f"GET XL FILES")
    image_files = []
    messages = []
    import_file = None
    files = form.getlist("files")
    for v in files:
        # print(f"XL FILES: {v}")
        filename = v.filename
        contents = await v.read()
        file_root, file_extension = os.path.splitext(filename)
        if file_extension == ".xlsx":
            messages.append(f"Excel file '{filename}' accepted")
            import_file = {"filename": filename, "contents": contents}
            application_logger.info(f"Processing upload file '{file_root}'")
        elif file_extension in [".png", "jpg", "jpeg"]:
            messages.append(f"Image file '{filename}' accepted")
            image_files.append({"filename": filename, "contents": contents})
            application_logger.info(f"Processing upload file '{file_root}'")
        else:
            messages.append(
                f"File '{filename}' was ignored, not .xlsx or an image file"
            )
    return import_file, image_files, messages


async def get_xl_files_os(form: File):
    # print(f"GET XL FILES OS")
    messages = []
    image_files = []
    import_file = None
    data = form.getlist("file_list_input")
    for uid in json.loads(data[0]):
        # print(f"XL OS FILE: {uid}")
        local_files = LocalFiles()
        file_root, file_extension, contents = local_files.download(uid)
        filename = f"{file_root}.{file_extension}"
        if file_extension == "xlsx":
            messages.append(f"Excel file '{filename}' accepted")
            import_file = {"filename": filename, "contents": contents}
            application_logger.info(f"Processing upload file '{file_root}'")
        elif file_extension in [".png", "jpg", "jpeg"]:
            messages.append(f"Image file '{filename}' accepted")
            image_files.append({"filename": filename, "contents": contents})
            application_logger.info(f"Processing upload file '{file_root}'")
        else:
            messages.append(f"File '{filename}' was ignored, not .docx file")
    return import_file, image_files, messages


def save_xl_files(import_file: dict, image_files: dict):
    files = DataFiles()
    uuid = files.new()
    saved_full_path, saved_filename = _save_file(files, import_file, "xlsx")
    for image_file in image_files:
        saved_full_path, saved_filename = _save_file(files, image_file, "image")
    return uuid


async def process_m11(request, templates, user, source="browser"):
    files_method = {
        "browser": get_m11_files,
        "pfda": get_m11_files_pfda,
        "os": get_m11_files_os,
    }
    try:
        form = await request.form()
        # print(f"FORM: {type(form)}")
        import_file, messages = await files_method[source](form)
        if import_file:
            uuid = save_m11_files(import_file)
            if uuid:
                run_background_task(process_word, uuid, user)
                return templates.TemplateResponse(
                    "import/partials/upload_success.html",
                    {
                        "request": request,
                        "filename": import_file["filename"],
                        "messages": messages,
                    },
                )
            else:
                messages.append("Failed to process the Word file")
                return templates.TemplateResponse(
                    "import/partials/upload_fail.html",
                    {
                        "request": request,
                        "filename": import_file["filename"],
                        "messages": messages,
                        "type": "Word",
                    },
                )
        else:
            messages.append("No Word file detected, file upload ignored")
            return templates.TemplateResponse(
                "import/partials/upload_fail.html",
                {
                    "request": request,
                    "filename": "",
                    "messages": messages,
                    "type": "Word",
                },
            )
    except Exception as e:
        application_logger.exception("Exception uploading files", e)
        return templates.TemplateResponse(
            "import/partials/upload_fail.html",
            {
                "request": request,
                "filename": "",
                "messages": [
                    "Exception raised while uploading files, see logs for more information"
                ],
                "type": "Word",
            },
        )


async def get_m11_files(form: FormData):
    messages = []
    import_file = None
    files = form.getlist("files")
    for v in files:
        # print(f"XL FILES: {v}")
        filename = v.filename
        contents = await v.read()
        file_root, file_extension = os.path.splitext(filename)
        if file_extension == ".docx":
            messages.append(f"Word file '{filename}' accepted")
            import_file = {"filename": filename, "contents": contents}
            application_logger.info(f"Processing upload file '{file_root}'")
        else:
            messages.append(f"File '{filename}' was ignored, not .docx file")
    return import_file, messages


async def get_m11_files_pfda(form: FormData):
    messages = []
    import_file = None
    # print(f"ITEMS: {form.items()}")
    # print(f"ITEMS: {form.getlist('file_list_input')}")
    data = form.getlist("file_list_input")
    for uid in json.loads(data[0]):
        # print(f"M11 PFDA FILE: {uid}")
        pfda = PFDAFiles()
        file_root, file_extension, contents = pfda.download(uid)
        # print(f"FILE: {file_root}, {file_extension}")
        filename = f"{file_root}.{file_extension}"
        if file_extension == "docx":
            messages.append(f"Word file '{filename}' accepted")
            import_file = {"filename": filename, "contents": contents}
            application_logger.info(f"Processing upload file '{file_root}'")
        else:
            messages.append(f"File '{filename}' was ignored, not .docx file")
    return import_file, messages


async def get_m11_files_os(form: FormData):
    messages = []
    import_file = None
    data = form.getlist("file_list_input")
    for uid in json.loads(data[0]):
        # print(f"M11 OS FILE: {uid}")
        local_files = LocalFiles()
        file_root, file_extension, contents = local_files.download(uid)
        filename = f"{file_root}.{file_extension}"
        if file_extension == "docx":
            messages.append(f"Word file '{filename}' accepted")
            import_file = {"filename": filename, "contents": contents}
            application_logger.info(f"Processing upload file '{file_root}'")
        else:
            messages.append(f"File '{filename}' was ignored, not .docx file")
    return import_file, messages


def save_m11_files(import_file: dict):
    return _save_files(import_file, "docx")


async def process_fhir(request, templates, user, source="browser"):
    files_method = {"browser": get_fhir_files, "pfda": None, "os": get_fhir_files_os}
    try:
        form = await request.form()
        import_file, messages = await files_method[source](form)
        if import_file:
            uuid = save_fhir_files(import_file)
            if uuid:
                run_background_task(process_fhir_v1, uuid, user)
                return templates.TemplateResponse(
                    "import/partials/upload_success.html",
                    {
                        "request": request,
                        "filename": import_file["filename"],
                        "messages": messages,
                    },
                )
            else:
                messages.append("Failed to process the Excel file")
                return templates.TemplateResponse(
                    "import/partials/upload_fail.html",
                    {
                        "request": request,
                        "filename": import_file["filename"],
                        "messages": messages,
                        "type": "JSON",
                    },
                )
        else:
            messages.append("No Word file detected, file upload ignored")
            return templates.TemplateResponse(
                "import/partials/upload_fail.html",
                {
                    "request": request,
                    "filename": "",
                    "messages": messages,
                    "type": "JSON",
                },
            )
    except Exception as e:
        application_logger.exception("Exception uploading files", e)
        return templates.TemplateResponse(
            "import/partials/upload_fail.html",
            {
                "request": request,
                "filename": "",
                "messages": [
                    "Exception raised while uploading files, see logs for more information"
                ],
                "type": "JSON",
            },
        )


async def get_fhir_files(form: File):
    messages = []
    import_file = None
    files = form.getlist("files")
    for v in files:
        # print(f"FHIR FILES: {v}")
        filename = v.filename
        contents = await v.read()
        file_root, file_extension = os.path.splitext(filename)
        if file_extension == ".json":
            messages.append(f"FHIR file '{filename}' accepted")
            import_file = {"filename": filename, "contents": contents}
            application_logger.info(f"Processing upload file '{file_root}'")
        else:
            messages.append(f"File '{filename}' was ignored, not .json file")
    return import_file, messages


async def get_fhir_files_os(form: File):
    messages = []
    import_file = None
    files = form.getlist("files")
    data = form.getlist("file_list_input")
    for uid in json.loads(data[0]):
        # print(f"FHIR OS FILE: {uid}")
        local_files = LocalFiles()
        file_root, file_extension, contents = local_files.download(uid)
        filename = f"{file_root}.{file_extension}"
        if file_extension == "json":
            messages.append(f"FHIR file '{filename}' accepted")
            import_file = {"filename": filename, "contents": contents}
            application_logger.info(f"Processing upload file '{file_root}'")
        else:
            messages.append(f"File '{filename}' was ignored, not .json file")
    return import_file, messages


def save_fhir_files(import_file: dict):
    return _save_files(import_file, "fhir")


def _save_files(import_file: dict, type: str) -> str:
    files = DataFiles()
    uuid = files.new()
    saved_full_path, saved_filename = _save_file(files, import_file, type)
    return uuid


def _save_file(files: DataFiles, import_file: dict, type: str) -> tuple[str, str]:
    filename = import_file["filename"]
    contents = import_file["contents"]
    return files.save(type, contents, filename)
