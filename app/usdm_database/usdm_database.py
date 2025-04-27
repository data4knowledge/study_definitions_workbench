# import json
# import yaml
from app.database.file_import import FileImport
from app.model.file_handling.data_files import DataFiles
from app.database.version import Version
from sqlalchemy.orm import Session

# from app.imports.import_manager import ImportManager
from usdm4_excel import USDM4Excel
from usdm3_excel import USDM3Excel


class USDMDatabase:
    def __init__(self, id: int, session: Session):
        self.id = id
        version = Version.find(id, session)
        file_import = FileImport.find(version.import_id, session)
        self.uuid = file_import.uuid
        self.type = file_import.type
        self._files = DataFiles(file_import.uuid)
        # self.m11 = (
        #     True
        #     if self.type in [ImportManager.M11_DOCX, ImportManager.FHIR_V1_JSON]
        #     else False
        # )
        # self._data = self._get_usdm()
        # self._extra = self._get_extra()

    def excel(self, version: str = "4"):
        usdm_fullpath, _, _ = self._files.path("usdm")
        excel_fullpath, excel_filename, _ = self._files.generic_path("xlsx")
        ue = USDM3Excel() if version == "3" else USDM4Excel()
        ue.to_excel(usdm_fullpath, excel_fullpath)
        return excel_fullpath, excel_filename, "application/vnd.ms-excel"

    # def _get_usdm(self):
    #     fullpath, filename, exists = self._files.path("usdm")
    #     data = open(fullpath)
    #     return json.load(data)

    # def _get_raw(self):
    #     fullpath, filename, exists = self._files.path("usdm")
    #     f = open(fullpath)
    #     return f.read()

    # def _get_extra(self):
    #     fullpath, filename, exists = self._files.path("extra")
    #     data = open(fullpath)
    #     return yaml.load(data, Loader=yaml.FullLoader)
