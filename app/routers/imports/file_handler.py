import os
import json
from fastapi import File
from starlette.datastructures import FormData
from app.model.file_handling.data_files import DataFiles
from app.model.file_handling.pfda_files import PFDAFiles
from app.model.file_handling.local_files import LocalFiles
from d4kms_generic import application_logger


class FileHandler:
    def __init__(self, single_file: bool, image_files: bool, ext: str, source: str):
        self.single_file = single_file
        self.image_files = image_files
        self.ext = ext if ext.startswith(".") else "." + ext
        self.source = source
        self._files_method = {
            "browser": self._get_files_browser,
            "pfda": self._get_files_pfda,
            "os": self._get_files_os,
        }

    async def get_files(self, form: File):
        # print(f"GET XL FILES")
        return await self._files_method[self.source](form)

    def save_files(self, main_file: dict, image_files: dict):
        files = DataFiles()
        uuid = files.new()
        saved_full_path, saved_filename = self._save_file(files, main_file, "xlsx")
        for image_file in image_files:
            saved_full_path, saved_filename = self._save_file(
                files, image_file, "image"
            )
        return uuid

    async def _get_files_browser(self, form: File):
        # print(f"GET XL FILES")
        image_files = []
        messages = []
        main_file = None
        files = form.getlist("files")
        for v in files:
            # print(f"XL FILES: {v}")
            filename = v.filename
            contents = await v.read()
            file_root, file_extension = os.path.splitext(filename)
            main_file, image_files = self._handle_file(
                file_extension,
                file_root,
                filename,
                contents,
                messages,
                main_file,
                image_files,
            )
        return main_file, image_files, messages

    async def _get_files_os(self, form: File):
        # print(f"GET XL FILES OS")
        messages = []
        image_files = []
        main_file = None
        data = form.getlist("file_list_input")
        for uid in json.loads(data[0]):
            # print(f"XL OS FILE: {uid}")
            local_files = LocalFiles()
            file_root, file_extension, contents = local_files.download(uid)
            filename = f"{file_root}.{file_extension}"
            main_file, image_files = self._handle_file(
                file_extension,
                file_root,
                filename,
                contents,
                messages,
                main_file,
                image_files,
            )
        return main_file, image_files, messages

    async def _get_files_pfda(self, form: FormData):
        messages = []
        main_file = None
        image_files = []
        data = form.getlist("file_list_input")
        for uid in json.loads(data[0]):
            pfda = PFDAFiles()
            file_root, file_extension, contents = pfda.download(uid)
            filename = f"{file_root}.{file_extension}"
            main_file, image_files = self._handle_file(
                file_extension,
                file_root,
                filename,
                contents,
                messages,
                main_file,
                image_files,
            )
        return main_file, image_files, messages

    def _handle_file(
        self,
        file_extension: str,
        file_root: str,
        filename: str,
        contents: bytes,
        messages: list,
        main_file: dict,
        image_files: list,
    ):
        if file_extension == self.ext:
            messages.append(f"File '{filename}' accepted")
            main_file = {"filename": filename, "contents": contents}
            application_logger.info(f"Processing upload file '{file_root}'")
        elif self.image_files and file_extension in [".png", "jpg", "jpeg"]:
            messages.append(f"Image file '{filename}' accepted")
            image_files.append({"filename": filename, "contents": contents})
            application_logger.info(f"Processing upload file '{file_root}'")
        else:
            messages.append(
                f"File '{filename}' was ignored, not '{self.ext}' file{' or image file' if self.image_files else ''}"
            )
        return main_file, image_files

    def _save_file(files: DataFiles, main_file: dict, type: str) -> tuple[str, str]:
        filename = main_file["filename"]
        contents = main_file["contents"]
        return files.save(type, contents, filename)
