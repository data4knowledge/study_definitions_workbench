from usdm_excel.globals import Globals
from app.model.raw_docx.raw_docx import RawDocx
from app.model.raw_docx.raw_table import RawTable
from app.model.raw_docx.raw_paragraph import RawParagraph
from d4kms_generic import application_logger
from app.model.m11_protocol.m11_utility import *

class M11IAmendment():
  
  def __init__(self, raw_docx: RawDocx, globals: Globals):
    self._globals = globals
    self._raw_docx = raw_docx
    self._id_manager = self._globals.id_manager
    self._cdisc_ct_library = self._globals.cdisc_ct_library
    self.enrollment = None
    self.primary_reason = None
    self.secondary_reason = None
    self.summary = None
    self.safety_impact = None
    self.robustness_impact = None
    self.changes = []

  def process(self):
    table = self._amendment_table()
    if table:
      self.enrollment = table_get_row(table, 'Enrolled at time ')
      self._reasons(table)
      self.summary = table_get_row(table, 'Amendment Summary')
      self.safety_impact = table_get_row(table, 'Is this amendment likely to have a substantial impact on the safety')
      self.robustness_impact = table_get_row(table, 'Is this amendment likely to have a substantial impact on the reliability')
    table = self._changes_table()
    if table:
      self.changes = self._changes(table)

  def _reasons(self, table):
    row = table.find_row('Amendment Summary')
    if row:
      self.primary_reason = self._find_reason('primary')
      self.secondary_reason = self._find_reason('secondary')

  def _changes(self, table):
    for index, row in enumerate(table.rows):
      if index == 0:
        continue
      self.changes.append({'description': row.cells[0].text(), 'rationale': row.cells[1].text(), 'section': row.cells[2].text()})

  def _amendment_table(self):
    amendment_table = None
    section = self._raw_docx.target_document.section_by_ordinal(1)
    tables = section.tables()
    for table in tables:
      row_three = tables.rows[2]
      if 'Amendment Summary' in row_three.cells[0].text():
        amendment_table = table
        break
    return amendment_table

  def _changes_table(self):
    result = None
    section = self._raw_docx.target_document.section_by_ordinal(1)
    for index, item in enumerate(section.items):
      if isinstance(item, RawParagraph):
        if item.text.upper().startswith('Overview of Changes in the Current Amendment'.upper()):
          result = section.next(index)
          if result:
            return result
    return result

  def _find_reason(self, row, key):
    reason_map = [
      {'code': 'C99904x1', 'decode': 'Regulatory Agency Request To Amend'},
      {'code': 'C99904x2', 'decode': 'New Regulatory Guidance'},
      {'code': 'C99904x3', 'decode': 'IRB/IEC Feedback'},
      {'code': 'C99904x4', 'decode': 'New Safety Information Available'},
      {'code': 'C99904x5', 'decode': 'Manufacturing Change'},
      {'code': 'C99904x6', 'decode': 'IMP Addition'},
      {'code': 'C99904x7', 'decode': 'Change In Strategy'},
      {'code': 'C99904x8', 'decode': 'Change In Standard Of Care'},
      {'code': 'C99904x9', 'decode': 'New Data Available (Other Than Safety Data)'},
      {'code': 'C99904x10', 'decode': 'Investigator/Site Feedback'},
      {'code': 'C99904x11', 'decode': 'Recruitment Difficulty'},
      {'code': 'C99904x12', 'decode': 'Inconsistency And/Or Error In The Protocol'},
      {'code': 'C99904x13', 'decode': 'Protocol Design Error'},
      {'code': 'C17649', 'decode': 'Other'},
      {'code': 'C48660', 'decode': 'Not Applicable'}
    ]
    cell = row.find_cell(key)
    if cell:
      parts = cell.text().split(' ')
      if len(parts) > 2:
        reason_text = parts[1]
        for reason in reason_map:
          if reason_text in reason['decode']:
            code = cdisc_ct_code(reason['code'], reason['decode'], self._cdisc_ct_library, self._id_manager)
            application_logger.info(f"Amednment reason '{reason_text}' decoded as '{reason['code']}', '{reason['decode']}'")
            return code
    code = cdisc_ct_code('C17649', 'Other', self._cdisc_ct_library, self._id_manager)
    application_logger.warning(f"Amendment reason '{reason_text}' not decoded")
    return code
