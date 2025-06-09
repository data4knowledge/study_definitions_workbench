import asyncio
import threading
from app.database.database import SessionLocal
from d4k_ms_base.logger import application_logger
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


class ImportManager:
    USDM_EXCEL = "USDM_EXCEL"
    M11_DOCX = "M11_DOCX"
    FHIR_V1_JSON = "FHIR_V1_JSON"
    # FHIR_V2_JSON = "FHIR_V2_JSON"
    USDM3_JSON = "USDM3_JSON"
    USDM4_JSON = "USDM4_JSON"

    def __init__(self, user: User, type: str) -> None:
        self.mapping = {
            self.USDM_EXCEL: {
                "processor": ImportExcel,
                "main_file_type": "xlsx",
                "main_file_ext": ".xlsx",
                "images": True,
            },
            self.M11_DOCX: {
                "processor": ImportWord,
                "main_file_type": "docx",
                "main_file_ext": ".docx",
                "images": False,
            },
            self.FHIR_V1_JSON: {
                "processor": ImportFhirV1,
                "main_file_type": "fhir",
                "main_file_ext": ".json",
                "images": False,
            },
            self.USDM3_JSON: {
                "processor": ImportUSDM3,
                "main_file_type": "usdm",
                "main_file_ext": ".json",
                "images": False,
            },
            self.USDM4_JSON: {
                "processor": ImportUSDM4,
                "main_file_type": "usdm",
                "main_file_ext": ".json",
                "images": False,
            },
        }
        self.user = user
        self.type = type
        self.processor = self.mapping[type]["processor"]
        self.main_file_type = self.mapping[type]["main_file_type"]
        self.main_file_ext = self.mapping[type]["main_file_ext"]
        self.images = self.mapping[type]["images"]
        self.files = None
        self.uuid = None
        self.original_filename = None

    @classmethod
    def imports_with_errors(cls) -> list[str]:
        return [
            cls.USDM_EXCEL,
            cls.M11_DOCX,
            cls.USDM3_JSON,
            cls.USDM4_JSON,
        ]

    @classmethod
    def is_m11_docx_import(cls, value: str) -> bool:
        return value == cls.M11_DOCX

    @classmethod
    def is_usdm_excel_import(cls, value: str) -> bool:
        return value == cls.USDM_EXCEL

    @classmethod
    def is_fhir_v1_import(cls, value: str) -> bool:
        return value == cls.FHIR_V1_JSON

    @classmethod
    def is_usdm3_json_import(cls, value: str) -> bool:
        return value == cls.USDM3_JSON

    @classmethod
    def is_usdm4_json_import(cls, value: str) -> bool:
        return value == cls.USDM4_JSON

    def save_files(self, main_file: dict, image_files: dict) -> str:
        if main_file:
            self.files = DataFiles()
            self.uuid = self.files.new()
            self.original_filename = main_file["filename"]
            # print(f"********** Original filename: {self.original_filename}")
            # print(f"********** Main file type: {self.main_file_type}")
            self._save_file(main_file, self.main_file_type)
            for image_file in image_files:
                self._save_file(image_file, "image")
        return self.uuid

    async def process(self) -> None:
        try:
            session = SessionLocal()
            file_import = None
            full_path, filename, exists = self.files.path(self.main_file_type)
            # print(f"********** Original filename: {self.original_filename}")
            file_import = FileImport.create(
                full_path,
                self.original_filename,
                "Processing",
                self.type,
                self.uuid,
                self.user.id,
                session,
            )
            processor: ImportProcessorBase = self.processor(
                self.type, self.uuid, full_path
            )
            result = await processor.process()
            if processor.errors:
                self.files.save("errors", processor.errors)
            if result:
                file_import.update_status("Saving", session)
                self.files.save("usdm", processor.usdm)
                self.files.save("extra", processor.extra)
                file_import.update_status("Create", session)
                Study.study_and_version(
                    processor.study_parameters, self.user, file_import, session
                )
                file_import.update_status("Success", session)
                session.close()
                await connection_manager.success(
                    f"Import of '{filename}' completed sucessfully", str(self.user.id)
                )
            else:
                file_import.update_status("Failed", session)
                session.close()
                await connection_manager.error(
                    f"Error encountered importing '{filename}', {processor.fatal_error}",
                    str(self.user.id),
                )
        except Exception as e:
            if file_import:
                file_import.update_status("Exception", session)
            application_logger.exception("Exception raised processing import", e)
            session.close()
            await connection_manager.error(
                f"Exception encountered importing '{filename}'", str(self.user.id)
            )

    def _save_file(self, file_details: dict, file_type: str) -> tuple[str, str]:
        filename = file_details["filename"]
        contents = file_details["contents"]
        return self.files.save(file_type, contents, filename)


def execute_import(import_manager: ImportManager) -> None:
    t = threading.Thread(target=asyncio.run, args=(import_manager.process(),))
    t.start()
