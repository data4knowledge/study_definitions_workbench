# import json
# import yaml
from app.database.file_import import FileImport
from app.model.file_handling.data_files import DataFiles
from app.database.version import Version
from sqlalchemy.orm import Session

# from app.imports.import_manager import ImportManager
from usdm4_excel import USDM4Excel


class USDMDatabase:
    def __init__(self, id: int, session: Session):
        self.id = id
        version = Version.find(id, session)
        file_import = FileImport.find(version.import_id, session)
        self.uuid = file_import.uuid
        self.type = file_import.type
        self._files = DataFiles(file_import.uuid)

    def excel(self):
        usdm_fullpath, _, _ = self._files.path("usdm")
        excel_fullpath, excel_filename, _ = self._files.generic_path("xlsx")
        ue = USDM4Excel()
        # Use the old CDISC single-workbook format for the while
        ue.to_excel(usdm_fullpath, excel_fullpath, format="legacy")
        return excel_fullpath, excel_filename, "application/vnd.ms-excel"
