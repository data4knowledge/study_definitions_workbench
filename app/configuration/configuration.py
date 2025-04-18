from d4k_ms_base.logger import application_logger
from d4k_ms_base.service_environment import ServiceEnvironment


class Configuration:
    def __init__(self):
        self._se = ServiceEnvironment()
        self.single_user: bool = self._single_user()
        self.multiple_user: bool = not self.single_user
        self.file_picker: dict = self._file_picker()
        self.address_server: str = self._se.get("ADDRESS_SERVER_URL")
        self.local_file_path: str = self._se.get("LOCALFILE_PATH")
        self.data_file_path = self._se.get("DATAFILE_PATH")
        self.mount_path = self._se.get("MNT_PATH")
        self.database_path = self._se.get("DATABASE_PATH")
        self.database_name = self._se.get("DATABASE_NAME")
        self.auth0_secret = self._se.get("AUTH0_SESSION_SECRET")

    def _single_user(self) -> bool:
        single = self._se.get("SINGLE_USER")
        application_logger.info(f"Single user mode '{single}'")
        return single.upper() in ["TRUE", "T", "Y", "YES"]

    def _file_picker(self) -> dict:
        picker = self._se.get("FILE_PICKER")
        application_logger.info(f"File picker '{picker}'")
        result = {
            "browser": picker.upper() == "BROWSER",
            "os": picker.upper() == "OS",
            "pfda": picker.upper() == "PFDA",
        }
        result["source"] = [k for k, v in result.items() if v][0]
        return result


application_configuration = Configuration()
