import asyncio
import threading

from d4k_ms_base.logger import application_logger
from usdm4_excel import USDM4Excel

from app.database.database import SessionLocal
from app.database.file_import import FileImport
from app.database.study import Study
from app.database.user import User
from app.imports.import_processors import (
    ImportCPT,
    ImportExcel,
    ImportFhirPRISM2,
    ImportFhirPRISM3,
    ImportLegacy,
    ImportM11,
    ImportProcessorBase,
    ImportUSDM4,
)
from app.model.connection_manager import connection_manager
from app.model.file_handling.data_files import DataFiles


class ImportManager:
    USDM_EXCEL = "USDM_EXCEL"
    M11_DOCX = "M11_DOCX"
    CPT_DOCX = "CPT_DOCX"
    LEGACY_PDF = "LEGACY_PDF"
    FHIR_PRISM2_JSON = "FHIR_PRISM2_JSON"
    FHIR_PRISM3_JSON = "FHIR_PRISM3_JSON"
    # USDM3_JSON imports were removed when v3 support was dropped; the
    # constant and its ``is_usdm3_json_import`` check remain so studies
    # imported historically still render (source pill, errors file).
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
                "processor": ImportM11,
                "main_file_type": "docx",
                "main_file_ext": ".docx",
                "images": False,
            },
            self.CPT_DOCX: {
                "processor": ImportCPT,
                "main_file_type": "docx",
                "main_file_ext": ".docx",
                "images": False,
            },
            self.LEGACY_PDF: {
                "processor": ImportLegacy,
                "main_file_type": "protocol",
                "main_file_ext": ".pdf",
                "images": False,
            },
            self.FHIR_PRISM2_JSON: {
                "processor": ImportFhirPRISM2,
                "main_file_type": "fhir_prism2",
                "main_file_ext": ".json",
                "images": False,
            },
            self.FHIR_PRISM3_JSON: {
                "processor": ImportFhirPRISM3,
                "main_file_type": "fhir_prism3",
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
        self.main_full_path = None
        self.save_error = None

    @classmethod
    def imports_with_errors(cls) -> list[str]:
        return [
            cls.USDM_EXCEL,
            cls.M11_DOCX,
            cls.CPT_DOCX,
            cls.LEGACY_PDF,
            cls.USDM3_JSON,
            cls.USDM4_JSON,
            cls.FHIR_PRISM2_JSON,
            cls.FHIR_PRISM3_JSON,
        ]

    @classmethod
    def is_m11_docx_import(cls, value: str) -> bool:
        return value == cls.M11_DOCX

    @classmethod
    def is_cpt_docx_import(cls, value: str) -> bool:
        return value == cls.CPT_DOCX

    @classmethod
    def is_legacy_pdf_import(cls, value: str) -> bool:
        return value == cls.LEGACY_PDF

    @classmethod
    def is_usdm_excel_import(cls, value: str) -> bool:
        return value == cls.USDM_EXCEL

    @classmethod
    def is_fhir_prism2_import(cls, value: str) -> bool:
        return value == cls.FHIR_PRISM2_JSON

    @classmethod
    def is_fhir_prism3_import(cls, value: str) -> bool:
        return value == cls.FHIR_PRISM3_JSON

    @classmethod
    def is_usdm3_json_import(cls, value: str) -> bool:
        return value == cls.USDM3_JSON

    @classmethod
    def is_usdm4_json_import(cls, value: str) -> bool:
        return value == cls.USDM4_JSON

    def save_files(
        self, main_file: dict, image_files: dict, extra_files: list[dict] = None
    ) -> str:
        """Save the uploaded files and record which one is the import's
        main file.

        ``extra_files`` carries any additional files sharing the main
        extension. Today that is the Excel multi-design format: a main
        workbook whose 'studyDesigns' row lists one external workbook
        per study design. All workbooks are saved into the same
        directory under their original filenames so ``usdm4_excel`` can
        resolve the references, and the main workbook is identified by
        its 'study' sheet — design workbooks don't have one. Single-file
        imports behave exactly as before.
        """
        if main_file:
            self.files = DataFiles()
            self.uuid = self.files.new()
            self.original_filename = main_file["filename"]
            saved = [self._save_file(main_file, self.main_file_type)]
            for extra_file in extra_files or []:
                saved.append(self._save_file(extra_file, self.main_file_type))
            for image_file in image_files:
                self._save_file(image_file, "image")
            if len(saved) == 1:
                self.main_full_path = saved[0][0]
            else:
                main = self._identify_main_workbook(saved)
                if main:
                    self.main_full_path, self.original_filename = main
                else:
                    self.save_error = (
                        "Could not identify the main workbook: exactly one of the "
                        "uploaded '.xlsx' files must be a main study workbook"
                    )
                    self.files.delete_all()
                    self.uuid = None
        return self.uuid

    def _identify_main_workbook(
        self, saved: list[tuple[str, str]]
    ) -> tuple[str, str] | None:
        """Return the (full_path, filename) of the one main study
        workbook among the saved files, or None if there isn't exactly
        one. Detection is delegated to usdm4_excel — the workbook
        layout is its knowledge, not SDW's."""
        excel = USDM4Excel()
        mains = []
        for full_path, filename in saved:
            try:
                if excel.is_main_workbook(full_path):
                    mains.append((full_path, filename))
            except Exception as e:
                application_logger.exception(
                    f"Exception inspecting workbook '{filename}'", e
                )
        return mains[0] if len(mains) == 1 else None

    async def process(self) -> None:
        try:
            session = SessionLocal()
            file_import = None
            full_path, filename = self.main_full_path, self.original_filename
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
