from usdm_excel.globals import Globals
from app.model.raw_docx.raw_docx import RawDocx
from app.model.raw_docx.raw_table import RawTable
from d4kms_generic import application_logger
from app.model.m11_protocol.m11_utility import *

class M11InclusionExclusion():
  
  def __init__(self, raw_docx: RawDocx, globals: Globals):
    self._globals = globals
    self._raw_docx = raw_docx
    self._id_manager = self._globals.id_manager
    self._cdisc_ct_library = self._globals.cdisc_ct_library
    self.inclusion = []
    self.exclusion = []

  def process(self):
    section = self._raw_docx.target_document.section_by_number('5.2')
    lists = section.lists()
    for item in lists[0].items:
      self.inclusion.append(item.to_html())
    section = self._raw_docx.target_document.section_by_number('5.3')
    lists = section.lists()
    for item in lists[0].items:
      self.exclusion.append(item.to_html())