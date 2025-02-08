import asyncio
import threading
from app.database.database import SessionLocal
from d4kms_generic import application_logger
from app.model.file_handling.data_files import DataFiles
from app.database.file_import import FileImport
from app.database.study import Study
from app.database.user import User
from app.model.connection_manager import connection_manager
from app.imports.import_processors import (
    ImportExcel,
    ImportWord,
    ImportFhirV1,
    ImportUSDM3,
    ImportUSDM4,
    ImportProcessorBase,
)


def execute_import(type: str, uuid: str, user: User) -> None:
    import_manager = ImportManager(uuid, user, type)
    t = threading.Thread(target=asyncio.run, args=(import_manager.process(),))
    t.start()


class ImportManager:
    USDM_EXCEL = "USDM_EXCEL"
    M11_DOCX = "M11_DOCX"
    FHIR_V1_JSON = "FHIR_V1_JSON"
    #FHIR_V2_JSON = "FHIR_V2_JSON"
    USDM3_JSON = "USDM3_JSON"
    USDM4_JSON = "USDM4_JSON"

    def __init__(self, uuid: str, user: User, type: str) -> None:
        self.mapping = {
            self.USDM_EXCEL: {"processor": ImportExcel, "main_file_type": "xlsx", 'main_file_ext': '.json', "images": True},
            self.M11_DOCX: {"processor": ImportWord, "main_file_type": "docx", 'main_file_ext': '.docx', "images": False},
            self.FHIR_V1_JSON: {"processor": ImportFhirV1, "main_file_type": "fhir", 'main_file_ext': '.json', "images": False},
            self.USDM3_JSON: {"processor": ImportUSDM3, "main_file_type": "usdm", 'main_file_ext': '.json', "images": False},
            self.USDM4_JSON: {"processor": ImportUSDM4, "main_file_type": "usdm", 'main_file_ext': '.json', "images": False},
        }
        self.uuid = uuid
        self.user = user
        self.type = type
        self.processor = self.mapping[type]["processor"]
        self.main_file_type = self.mapping[type]["main_file_type"]
        self.main_file_ext = self.mapping[type]["main_file_ext"]
        self.images = self.mapping[type]["images"]
        self.files = None

    def save_files(self, main_file: dict, image_files: dict) -> str:
        self.files = DataFiles()
        uuid = self.files.new()
        self._save_file(self.files, main_file, self.main_file_type)
        for image_file in image_files:
            self._save_file(self.files, image_file, "image")
        return uuid

    async def process(self) -> None:
        try:
            session = SessionLocal()
            file_import = None
            full_path, filename, exists = self.files.path(self.type)
            file_import = FileImport.create(
                full_path,
                filename,
                "Processing",
                self.type,
                self.uuid,
                self.user.id,
                session,
            )
            processor: ImportProcessorBase = self.processor(self.type, full_path)
            parameters = await processor.process()
            
            file_import.update_status("Saving", session)
            if processor.errors:
                self.files.save("errors", processor.errors)
            self.files.save("usdm", processor.usdm)
            self.files.save("extra", processor.extra)

            file_import.update_status("Create", session)
            Study.study_and_version(parameters, self.user, file_import, session)
            file_import.update_status("Success", session)
            session.close()
            await connection_manager.success(
                "Import completed sucessfully", str(self.user.id)
            )
        except Exception as e:
            if file_import:
                file_import.update_status("Exception", session)
            application_logger.exception(f"Exception raised processing import", e)
            session.close()
            await connection_manager.error(
                "Error encountered importing", str(self.user.id)
            )

    def _save_file(self, file_details: dict, file_type: str) -> tuple[str, str]:
        filename = file_details["filename"]
        contents = file_details["contents"]
        return self.files.save(file_type, contents, filename)