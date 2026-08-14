import json
import os

from d4k_ms_base.logger import application_logger
from fastapi import File, Request
from starlette.datastructures import FormData

from app.model.file_handling.local_files import LocalFiles
from app.model.file_handling.pfda_files import PFDAFiles


class FormHandler:
    def __init__(self, request: Request, image_files: bool, ext: str, source: str):
        self.request = request
        self.image_files = image_files
        self.ext = ext if ext.startswith(".") else "." + ext
        self.source = source
        # Additional files sharing the main extension (beyond the first).
        # Used by the Excel import flow where a multi-design study is
        # uploaded as a main workbook plus one workbook per study design.
        self.extra_files: list[dict] = []
        self._files_method = {
            "browser": self._get_files_browser,
            "pfda": self._get_files_pfda,
            "os": self._get_files_os,
        }

    async def get_files(self):
        form = await self.request.form()
        return await self._files_method[self.source](form)

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
            filename = f"{file_root}{file_extension}"
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
            if main_file is None:
                main_file = {"filename": filename, "contents": contents}
            else:
                self.extra_files.append({"filename": filename, "contents": contents})
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
