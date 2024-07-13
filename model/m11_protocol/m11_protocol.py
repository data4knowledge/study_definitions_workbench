from d4kms_generic import application_logger
from model.docx.document import Document
from model.docx.table import Table
from model.m11_protocol.m11_protocol_to_usdm import M11ProtocolToUSDM

class M11Protocol():

  def __init__(self, raw: Document):
    self.raw = raw
    self.sections = []
    self.full_title = None
    self.sponsor_protocol_identifier = None
    self.original_protocol = None
    self.version_number = None
    self.amendment_identifier = None
    self.amendment_scope = None
    self.compound_codes = None
    self.compund_names = None
    self.trial_phase_raw = None
    self.short_title = None
    self.sponsor_name_and_address = None
    self.regulatory_agency_identifiers = None
    self.sponsor_approval_date = None
    self._decode_title_page()
    self._build_sections()
    #print(f"Titles {self.full_title}, {self.short_title}")

  def to_usdm(self):
    m11_to_usdm = M11ProtocolToUSDM(self)
    return m11_to_usdm.to_usdm()

  def _decode_title_page(self):
    section = self.raw.section_by_ordinal(1)
    tables = section.tables()
    table = tables[0]
    self.full_title = self._table_get_row(table, 'Full Title')
    self.sponsor_protocol_identifier = self._table_get_row(table, 'Sponsor Protocol Identifier')
    self.original_protocol = self._table_get_row(table, 'Original Protocol')
    self.version_number = self._table_get_row(table, 'Version Number')
    self.amendment_identifier = self._table_get_row(table, 'Amendment Identifier')
    self.amendment_scope = self._table_get_row(table, 'Amendment Scope')
    self.compound_codes = self._table_get_row(table, 'Compound Code(s)')
    self.compund_names = self._table_get_row(table, 'Compound Name(s)')
    self.trial_phase_raw = self._table_get_row(table, 'Trial Phase')
    self.short_title = self._table_get_row(table, 'Short Title')
    self.sponsor_name_and_address = self._table_get_row(table, 'Sponsor Name and Address')
    self.regulatory_agency_identifiers = self._table_get_row(table, 'Regulatory Agency Identifier Number(s)')
    self.sponsor_approval_date = self._table_get_row(table, 'Sponsor Approval Date')
  
  def _build_sections(self):
    for section in self.raw.sections:
      self.sections.append(section)

  def _table_get_row(self, table: Table, key: str) -> str:
    for row in table.rows:
      if row.cells[0].is_text():
        if row.cells[0].text().upper().startswith(key.upper()):
          return row.cells[1].text().strip()
    return None