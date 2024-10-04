from usdm_excel.globals import Globals
from app.model.raw_docx.raw_docx import RawDocx
from d4kms_generic import application_logger
from app.model.m11_protocol.m11_utility import *

class M11Styles():
  
  ICH_HEADERS = [
    ('INTERNATIONAL COUNCIL FOR HARMONISATION OF TECHNICAL REQUIREMENTS FOR PHARMACEUTICALS FOR HUMAN USE', 'ich-m11-header-1'),
    ('ICH HARMONISED GUIDELINE', 'ich-m11-header-2'),
    ('Clinical electronic Structured Harmonised Protocol', 'ich-m11-header-3'),
    ('(CeSHarP)', 'ich-m11-header-4'),
    ('Example', 'ich-m11-header-4')
  ]
  DESIGN_ITEMS = [
    ('Number of Arms', 'ich-m11-overall-design-title'),
    ('Trial Blind Schema', 'ich-m11-overall-design-title'),
    ('Number of Participants', 'ich-m11-overall-design-title'),
    ('Duration', 'ich-m11-overall-design-title'),
    ('Committees', 'ich-m11-overall-design-title'),
    ('Blinded Roles', 'ich-m11-overall-design-title')
  ]

  def __init__(self, raw_docx: RawDocx, globals: Globals):
    self._globals = globals
    self._raw_docx = raw_docx

  def process(self):
    self._decode_ich_header()
    self._decode_trial_design_summary()

  def _decode_ich_header(self):
    section = self._raw_docx.target_document.section_by_ordinal(1)
    for header in self.ICH_HEADERS:
      items = section.find(header[0])
      for item in items:
        item.add_class(header[1])

  def _decode_trial_design_summary(self):
    section = self._raw_docx.target_document.section_by_number('1.1.2')
    tables = section.tables()
    table = tables[0]
    table.replace_class('ich-m11-table', 'ich-m11-overall-design-table')
    for design_item in self.DESIGN_ITEMS:
      items = section.find_at_start(design_item[0])
      for item in items:
        item.add_span(design_item[0], design_item[1])
  