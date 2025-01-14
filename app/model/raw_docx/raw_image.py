import os
import base64
from d4kms_generic import application_logger


class RawImage:
    FILE_TYPE_MAP = {".png": "png", ".jpg": "jpg", ".jpeg": "jpg"}

    def __init__(self, filepath: str):
        self.filepath = filepath

    def to_html(self):
        try:
            file_root, file_extension = os.path.splitext(self.filepath)
            if file_extension in self.FILE_TYPE_MAP:
                file_type = self.FILE_TYPE_MAP[file_extension]
                with open(self.filepath, "rb") as image_file:
                    data = base64.b64encode(image_file.read())
                decoded = data.decode("ascii")
                return f'<img alt="alt text" src="data:image/{file_type};base64,{decoded}"/>'
            else:
                return f"""<p style="color:red">Note: Unable to process embedded image of type '{file_extension}', image ignored.</p>"""
        except Exception as e:
            application_logger.exception("Exception converting image", e)
            return (
                """<p style="color:red">Note: Error encountered processing image.</p>"""
            )
