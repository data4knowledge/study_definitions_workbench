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
        # Secret used to sign the session cookie. Historically named
        # AUTH0_SESSION_SECRET; SESSION_SECRET takes precedence if set so
        # the Auth0 naming can be retired without breaking deployments.
        self.auth0_secret = self._se.get("AUTH0_SESSION_SECRET")
        self.session_secret = self._se.get("SESSION_SECRET") or self.auth0_secret
        # Email-code (magic code) login configuration.
        self.app_name = self._se.get("APP_NAME") or "Study Definitions Workbench"
        self.code_length = int(self._se.get("CODE_LENGTH") or 6)
        self.code_expiry_minutes = int(self._se.get("CODE_EXPIRY_MINUTES") or 10)
        self.smtp_host = self._se.get("SMTP_HOST")
        self.smtp_port = int(self._se.get("SMTP_PORT") or 587)
        self.smtp_user = self._se.get("SMTP_USER")
        self.smtp_password = self._se.get("SMTP_PASSWORD")
        self.smtp_from = self._se.get("SMTP_FROM") or self.smtp_user
        # Address notified whenever someone self-registers. Empty disables.
        self.registration_notify_email = self._se.get("REGISTRATION_NOTIFY_EMAIL")
        # When no SMTP host is configured (or EMAIL_DEV_MODE is truthy) the
        # login code is logged instead of emailed, so the app is usable in
        # local/dev without a mail server.
        self.email_dev_mode = self._email_dev_mode()
        # Optional fixed login code used ONLY in dev mode (e.g. for
        # Playwright). When set and email_dev_mode is on, generate_code
        # returns this instead of a random code. Never used in production
        # (email_dev_mode is off there).
        self.dev_login_code = self._se.get("DEV_LOGIN_CODE")
        # CDISC CORE validation cache — persistent directory for the
        # resources the CDISC CORE engine downloads (JSONata files, XSD
        # schemas, rules, CT packages). Without this, the cache lands in
        # platformdirs.user_cache_dir() which in a Docker container is
        # ephemeral (wiped on every restart). Setting this to a path on
        # the mounted volume keeps the cache persistent across restarts.
        # Empty string falls through to the USDM4 platform default, so a
        # deployment that hasn't been upgraded still works.
        self.cdisc_core_cache_path = self._se.get("CDISC_CORE_CACHE_PATH")

    def _email_dev_mode(self) -> bool:
        flag = self._se.get("EMAIL_DEV_MODE")
        if flag is not None:
            return flag.upper() in ["TRUE", "T", "Y", "YES"]
        # Default: dev mode whenever no SMTP host has been configured.
        return not self.smtp_host

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
