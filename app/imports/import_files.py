from app.imports.file_handler import FileHandler
from d4kms_generic import application_logger
from app.imports.import_manager import execute_import

class ImportFiles:
    TYPE_MAPPING = {
        "xlsx": ".xlsx",
        "docx": ".docx",
        "fhir": ".json",
        "usdm3": ".json",
        "usdm4": ".json",
    }

    def __init__(self, type: str, source: str):
        self.ext = self.TYPE_MAPPING[type]
        self.source = source
        self.type = type

    async def process(self, request, templates, user):
        try:
            files_handler = FileHandler(
                single_file=True, image_files=True, ext=self.ext, source=self.source
            )
            form = await request.form()
            main_file, image_files, messages = await files_handler.get_files(form)
            if main_file:
                uuid = files_handler.save_files(main_file, image_files, self.type)
                if uuid:
                    execute_import(self.type, uuid, user)
                    return templates.TemplateResponse(
                        "import/partials/upload_success.html",
                        {
                            "request": request,
                            "filename": main_file["filename"],
                            "messages": messages,
                        },
                    )
                else:
                    messages.append("Failed to process the Excel file")
                    return templates.TemplateResponse(
                        "import/partials/upload_fail.html",
                        {
                            "request": request,
                            "filename": main_file["filename"],
                            "messages": messages,
                            "type": self.type,
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
                        "type": self.type,
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
