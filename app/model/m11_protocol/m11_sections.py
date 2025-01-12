from usdm_excel.globals import Globals
from app.model.raw_docx.raw_docx import RawDocx
from app.model.m11_protocol.m11_utility import *


class M11Sections:
    def __init__(self, raw_docx: RawDocx, globals: Globals):
        self._globals = globals
        self._raw_docx = raw_docx
        self.sections = []

    def process(self):
        for section in self._raw_docx.target_document.sections:
            self.sections.append(section)
