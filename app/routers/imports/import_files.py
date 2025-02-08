from app.routers.imports.file_handler import FileHandler
from d4kms_generic import application_logger
from app.utility.background import (
    process_excel,
    process_word,
    process_fhir_v1,
    run_background_task,
)


class ImportFiles:
    TYPE_MAPPING = {
        "Excel": ".xlsx",
        "Word": ".docx",
        "FHIR": ".json",
        "USDM": ".json",
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
                uuid = files_handler.save_files(main_file, image_files)
                if uuid:
                    run_background_task(process_excel, uuid, user)
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
