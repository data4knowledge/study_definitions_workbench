import os
import json
import subprocess
from d4k_ms_base.logger import application_logger


class PFDAFiles:
    def dir(self, dir):
        try:
            args = ["pfda", "ls", "-json"]
            result = subprocess.run(args, capture_output=True, text=True)
            response = json.loads(result.stdout)
            if "error" in response:
                application_logger.error(f"pFDA error: {response['error']}")
                return False, {}, response["error"]
            else:
                application_logger.info(f"pFDA file list response: {response}")
                return True, {"files": response["files"]}, ""
        except Exception as e:
            application_logger.exception("pFDA exception", e)
            return (
                False,
                {},
                f"Exception '{e}' raised, check the logs for more information",
            )

    def download(self, uid: str):
        target = self._files.path()
        args = [
            "pfda",
            "download",
            uid,
            "-output",
            f"{target}",
            "-json",
            "-overwrite",
            "true",
        ]
        # print(f"ARGS: {args}")
        result = subprocess.run(args, capture_output=True, text=True)
        # print(f"RESULT: {result}")
        application_logger.info(f"PFDA download: {result.stdout}")
        files = json.loads(result.stdout)
        file_root, file_extension, contents = self._read(files["result"])
        return file_root, file_extension, contents

    def _read(self, full_path):
        # print(f"FULL_PATH: {full_path}")
        head_tail = os.path.split(full_path)
        stem, extension = self._stem_and_extension(head_tail[1])
        with open(full_path, "rb") as stream:
            return stem, extension, stream.read()

    def _stem_and_extension(self, filename):
        result = os.path.splitext(filename)
        return result[0], result[1][1:]
