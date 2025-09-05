import os
import json
import csv
import shutil
import yaml
from uuid import uuid4
from d4k_ms_base.logger import application_logger
from app.configuration.configuration import application_configuration


class DataFiles:
    class LogicError(Exception):
        pass

    def __init__(self, uuid=None):
        self.media_type = {
            "xlsx": {
                "method": self._save_excel_file,
                "use_original": True,
                "filename": "xl",
                "extension": "xlsx",
            },
            "docx": {
                "method": self._save_word_file,
                "use_original": True,
                "filename": "doc",
                "extension": "docx",
            },
            "usdm": {
                "method": self._save_json_file,
                "use_original": False,
                "filename": "usdm",
                "extension": "json",
            },
            "fhir_prism2": {
                "method": self._save_json_file,
                "use_original": False,
                "filename": "fhir_prism2",
                "extension": "json",
            },
            "fhir_atlanta": {
                "method": self._save_json_file,
                "use_original": False,
                "filename": "fhir_atlanta",
                "extension": "json",
            },
            "fhir_madrid": {
                "method": self._save_json_file,
                "use_original": False,
                "filename": "fhir_madrid",
                "extension": "json",
            },
            "fhir_prism3": {
                "method": self._save_json_file,
                "use_original": False,
                "filename": "fhir_prism3",
                "extension": "json",
            },
            "fhir_soa": {
                "method": self._save_json_file,
                "use_original": False,
                "filename": "fhir_soa",
                "extension": "json",
            },
            "errors": {
                "method": self._save_csv_file,
                "use_original": False,
                "filename": "errors",
                "extension": "csv",
            },
            "protocol": {
                "method": self._save_pdf_file,
                "use_original": True,
                "filename": "protocol",
                "extension": "pdf",
            },
            "highlight": {
                "method": self._save_html_file,
                "use_original": False,
                "filename": "highlight",
                "extension": "html",
            },
            "image": {
                "method": self._save_image_file,
                "use_original": True,
                "filename": "",
                "extension": "",
            },
            "extra": {
                "method": self._save_yaml_file,
                "use_original": False,
                "filename": "extra",
                "extension": "yaml",
            },
        }
        self.uuid = uuid
        self.dir = application_configuration.data_file_path

    @classmethod
    def clean_and_tidy(cls):
        dir = application_configuration.mount_path
        keep = [
            application_configuration.data_file_path,
            application_configuration.database_path,
            application_configuration.local_file_path,
        ]
        application_logger.info(f"Running clean and tidy on '{dir}'")
        try:
            for file in os.listdir(dir):
                path = os.path.join(dir, file)
                # print(f"ITEM: {file} {path}")
                if os.path.isfile(path):
                    # print(f"FILE: {file}")
                    try:
                        path = os.path.join(dir, file)
                        os.unlink(path)
                        application_logger.info(
                            f"Unlinked file '{path}' during clean and tidy"
                        )
                    except Exception as e:
                        application_logger.exception(
                            f"Exception unlinking file '{path}' during clean and tidy dir '{dir}'",
                            e,
                        )
                else:
                    # print(f"DIR: {file}")
                    path = os.path.join(dir, file)
                    if path not in keep:
                        try:
                            shutil.rmtree(path)
                            application_logger.info(
                                f"Removed dir '{path}' during clean and tidy"
                            )
                        except Exception as e:
                            application_logger.exception(
                                f"Exception deleting '{path}' during clean and tidy dir '{dir}'",
                                e,
                            )
                    else:
                        application_logger.info(
                            f"Keeping dir '{path}' during clean and tidy"
                        )
            application_logger.info("Deleted datafiles dir")
            return True
        except Exception as e:
            application_logger.exception(f"Exception during clean and tidy '{dir}'", e)
            return False

    @classmethod
    def check(cls):
        dir = application_configuration.data_file_path
        application_logger.info("Checking datafiles dir exists")
        try:
            os.mkdir(dir)
            application_logger.info("Datafiles dir created")
            return True
        except FileExistsError:
            application_logger.info("Datafiles dir exists")
        except Exception as e:
            application_logger.exception(
                f"Exception checking/creating datafiles dir '{dir}'", e
            )
            return False

    def new(self):
        self.uuid = str(uuid4())
        if not self._create_dir():
            self.uuid = None
        return self.uuid

    def save(self, type: str, contents, filename: str = "") -> tuple[str, str]:
        filename = (
            filename
            if self.media_type[type]["use_original"]
            else self._form_filename(type)
        )
        full_path = self.media_type[type]["method"](contents, filename)
        return full_path, filename

    def read(self, type):
        full_path = self._file_path(self._form_filename(type))
        with open(full_path, "r") as stream:
            return stream.read()

    def path(self, type):
        exists = True
        if self.media_type[type]["use_original"]:
            files = self._dir_files_by_extension(self.media_type[type]["extension"])
            # print(f"FILES: {files}")
            if len(files) == 1:
                filename = files[0]
                full_path = self._file_path(filename)
            else:
                application_logger.error(
                    f"Found multiple files for type '{type}' when forming path. Files = {files}"
                )
                raise self.LogicError
        else:
            filename = self._form_filename(type)
            full_path = self._file_path(filename)
            if not os.path.exists(full_path):
                exists = False
        return full_path, filename, exists

    def generic_path(self, type):
        filename = self._form_filename(type)
        full_path = self._file_path(filename)
        exists = os.path.exists(full_path)
        return full_path, filename, exists

    def delete_all(self):
        try:
            for root, dirs, files in os.walk(self.dir):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
            application_logger.info("Deleted datafiles dir")
            return True
        except Exception as e:
            application_logger.exception(
                f"Exception deleting datafiles dir '{self.dir}'", e
            )
            return False

    def delete(self):
        path = self._dir_path()
        try:
            shutil.rmtree(path)
            application_logger.info(f"Deleted study dir '{path}'")
            return True
        except Exception as e:
            application_logger.exception(f"Exception deleting study dir '{path}'", e)
            return False

    def _save_excel_file(self, contents, filename):
        self._save_binary_file(contents, filename)

    def _save_word_file(self, contents, filename):
        self._save_binary_file(contents, filename)

    def _save_binary_file(self, contents, filename):
        try:
            full_path = self._file_path(filename)
            with open(full_path, "wb") as f:
                f.write(contents)
            return full_path
        except Exception as e:
            application_logger.exception("Exception saving source file", e)

    def _save_image_file(self, contents, filename):
        try:
            full_path = self._file_path(filename)
            with open(full_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            application_logger.exception("Exception saving source file", e)

    def _save_json_file(self, contents, filename):
        try:
            full_path = self._file_path(filename)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(json.loads(contents), indent=2))
            return full_path
        except Exception as e:
            application_logger.exception("Exception saving results file", e)

    def _save_yaml_file(self, contents, filename):
        try:
            full_path = self._file_path(filename)
            with open(full_path, "w") as f:
                yaml.dump(contents, f, default_flow_style=False)
            return full_path
        except Exception as e:
            application_logger.exception("Exception saving results file", e)

    def _save_pdf_file(self, contents, filename):
        try:
            full_path = self._file_path(filename)
            with open(full_path, "w+b") as f:
                f.write(contents)
            return full_path
        except Exception as e:
            application_logger.exception("Exception saving PDF file", e)

    def _save_html_file(self, contents, filename):
        try:
            full_path = self._file_path(filename)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(contents)
            return full_path
        except Exception as e:
            application_logger.exception("Exception saving timeline file", e)

    def _save_csv_file(self, contents, filename):
        if not contents:
            contents = [{"message": "No errors"}]
        try:
            full_path = self._file_path(filename)
            with open(full_path, "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(contents[0].keys()))
                writer.writeheader()
                writer.writerows(contents)
            return full_path
        except Exception as e:
            application_logger.exception("Exception saving error file", e)

    def _create_dir(self):
        try:
            os.mkdir(os.path.join(self.dir, self.uuid))
            return True
        except Exception as e:
            application_logger.exception(f"Exception creating dir '{self.uuid}'", e)
            return False

    def _dir_path(self):
        return os.path.join(self.dir, self.uuid)

    def _file_path(self, filename):
        return os.path.join(self.dir, self.uuid, filename)

    def _form_filename(self, type):
        return (
            f"{self.media_type[type]['filename']}.{self.media_type[type]['extension']}"
        )

    def _dir_files_by_extension(self, extension):
        dir = self._dir_files()
        return [f for f in dir if self._extension(f) == extension]

    def _dir_files(self):
        path = self._dir_path()
        return [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    def _stem_and_extension(self, filename):
        result = os.path.splitext(filename)
        return result[0], result[1][1:]

    def _extension(self, filename):
        result = os.path.splitext(filename)
        return result[1][1:]
