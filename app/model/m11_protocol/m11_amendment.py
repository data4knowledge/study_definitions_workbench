import re
from usdm_excel.globals import Globals
from usdm_model.geographic_scope import SubjectEnrollment
from usdm_model.quantity import Quantity
from app.model.raw_docx.raw_docx import RawDocx
from app.model.raw_docx.raw_table import RawTable
from app.model.raw_docx.raw_paragraph import RawParagraph
from d4kms_generic import application_logger
from app.model.m11_protocol.m11_utility import *

class M11IAmendment():

  OTHER_REASON = 'No reason text found'

  def __init__(self, raw_docx: RawDocx, globals: Globals):
    self._globals = globals
    self._raw_docx = raw_docx
    self._id_manager = self._globals.id_manager
    self._cdisc_ct_library = self._globals.cdisc_ct_library
    other_code = cdisc_ct_code('C17649', 'Other', self._cdisc_ct_library, self._id_manager)
    self.enrollment = self._build_enrollment(0, '')
    self.primary_reason = {'code': other_code, 'other_reason': self.OTHER_REASON}
    self.secondary_reason = {'code': other_code, 'other_reason': self.OTHER_REASON}
    self.summary = ''
    self.safety_impact = False
    self.robustness_impact = False
    self.changes = []

  def process(self):
    table = self._amendment_table()
    if table:
      self._enrollment(table)
      self._reasons(table)
      self.summary = table_get_row_html(table, 'Amendment Summary')
      if self.summary:
        application_logger.info(f"Amendment summary found")
      self.safety_impact = False
      x = table_get_row(table, 'Is this amendment likely to have a substantial impact on the safety')
      self.robustness_impact = False
      x = table_get_row(table, 'Is this amendment likely to have a substantial impact on the reliability')
    table = self._changes_table()
    if table:
      self.changes = self._changes(table)

  def _reasons(self, table):
    row = table.find_row('Reason(s) for Amendment:')
    if row:
      self.primary_reason = self._find_reason(row, 'primary')
      self.secondary_reason = self._find_reason(row, 'secondary')

  def _changes(self, table):
    for index, row in enumerate(table.rows):
      if index == 0:
        continue
      self.changes.append({'description': row.cells[0].text(), 'rationale': row.cells[1].text(), 'section': row.cells[2].text()})

  def _amendment_table(self):
    section = self._raw_docx.target_document.section_by_ordinal(1)
    for index, item in enumerate(section.items):
      if isinstance(item, RawParagraph):
        if text_within('The table below describes the current amendment', item.text):
          table = section.next_table(index)
          application_logger.info(f"Amendment table {'' if table else 'not '}found")
          return table
    return None

  def _changes_table(self):
    section = self._raw_docx.target_document.section_by_ordinal(1)
    for index, item in enumerate(section.items):
      if isinstance(item, RawParagraph):
        if text_within('Overview of Changes in the Current Amendment', item.text):
          table = section.next_table(index)
          application_logger.info(f"Changes table {'' if table else 'not '}found")
          return table
    return None

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
    #print(f"ROW: {row.to_html()}")
    cell = row.find_cell(key)
    if cell:
      reason = cell.text()
      parts = cell.text().split(' ')
      if len(parts) > 2:
        reason_text = parts[1]
        for reason in reason_map:
          if reason_text in reason['decode']:
            application_logger.info(f"Amednment reason '{reason_text}' decoded as '{reason['code']}', '{reason['decode']}'")
            code = cdisc_ct_code(reason['code'], reason['decode'], self._cdisc_ct_library, self._id_manager)
            return {'code': code, 'other_reason': ''}
      application_logger.warning(f"Unable to decode amendment reason '{reason}'")      
      code = cdisc_ct_code('C17649', 'Other', self._cdisc_ct_library, self._id_manager)
      return {'code': code, 'other_reason': parts[1].strip()}
    application_logger.warning(f"Amendment reason '{key}' not decoded")
    code = cdisc_ct_code('C17649', 'Other', self._cdisc_ct_library, self._id_manager)
    return {'code': code, 'other_reason': 'No reason text found'}

  def _enrollment(self, table):
    text = table_get_row(table, 'Enrolled at time ')  
    number = re.findall('[0-9]+', text)
    value = int(number[0]) if number else 0
    unit = '%' if '%' in text else ''
    self.enrollment = self._build_enrollment(value, unit)

  def _build_enrollment(self, value, unit):
    global_code = cdisc_ct_code('C68846', 'Global', self._cdisc_ct_library, self._id_manager)
    percent_code = cdisc_ct_code('C25613', 'Percentage', self._cdisc_ct_library, self._id_manager)
    unit_code = percent_code if unit == '%' else None
    unit_alias = alias_code(unit_code, self._id_manager) if unit_code else None
    quantity = model_instance(Quantity, {'value': value, 'unit': unit_alias}, self._id_manager)
    params = {
      'type': global_code,
      'code': None,
      'quantity': quantity
    }
    return model_instance(SubjectEnrollment, params, self._id_manager)
