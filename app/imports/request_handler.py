from fastapi import Request
from app.imports.form_handler import FormHandler
from d4k_ms_base.logger import application_logger
from app.imports.import_manager import ImportManager, execute_import


class RequestHandler:
    def __init__(self, type: str, source: str):
        self.source = source
        self.type = type

    async def process(self, request: Request, templates, user):
        try:
            import_manager = ImportManager(user, self.type)
            form_handler = FormHandler(
                request,
                import_manager.images,
                import_manager.main_file_ext,
                self.source,
            )
            main_file, image_files, messages = await form_handler.get_files()
            uuid = import_manager.save_files(main_file, image_files)
            if uuid:
                execute_import(import_manager)
                return templates.TemplateResponse(
                    "import/partials/upload_success.html",
                    {
                        "request": request,
                        "filename": main_file["filename"],
                        "messages": messages,
                        "route": "/index",
                        "label": "Home"
                    },
                )
            else:
                messages.append("Failed to process the import file(s)")
                return templates.TemplateResponse(
                    "import/partials/upload_fail.html",
                    {
                        "request": request,
                        "filename": main_file["filename"],
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
