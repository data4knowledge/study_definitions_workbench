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
    PROCESSOR_MAPPING = {
        "xlsx": {"processor": ImportExcel, "files": "xlsx"},
        "docx": {"processor": ImportWord, "files": "docx"},
        "fhir": {"processor": ImportFhirV1, "files": "fhir"},
        "usdm3": {"processor": ImportUSDM3, "files": "usdm"},
        "usdm4": {"processor": ImportUSDM4, "files": "usdm"},
    }

    def __init__(self, uuid: str, user: User, type: str) -> None:
        self.uuid = uuid
        self.user = user
        self.type = type
        self.processor = self.PROCESSOR_MAPPING[type]["processor"]
        self.file_type = self.PROCESSOR_MAPPING[type]["files"]

    async def process(self) -> None:
        try:
            session = SessionLocal()
            file_import = None
            files = DataFiles(self.uuid)
            full_path, filename, exists = files.path(self.file_type)
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
                files.save("errors", processor.errors)
            files.save("usdm", processor.usdm)
            files.save("extra", processor.extra)

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
