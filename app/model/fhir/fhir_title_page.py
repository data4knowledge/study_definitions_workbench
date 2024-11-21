import re
import warnings
from bs4 import BeautifulSoup   
from d4kms_generic import application_logger

class FHIRTitlePage():

  def __init__(self, sections: list, items: list):
    table = self._title_table(sections, items)
    #print(f"TABLE: {table}")
    self.full_title = self._table_get_row(table, 'Full Title')
    self.acronym = self._table_get_row(table, 'Acronym')
    self.sponsor_protocol_identifier = self._table_get_row(table, 'Sponsor Protocol Identifier')
    self.original_protocol = self._table_get_row(table, 'Original Protocol')
    self.version_number = self._table_get_row(table, 'Version Number')
    self.amendment_identifier = self._table_get_row(table, 'Amendment Identifier')
    self.amendment_scope = self._table_get_row(table, 'Amendment Scope')
    self.compound_codes = self._table_get_row(table, 'Compound Code(s)')
    self.compound_names = self._table_get_row(table, 'Compound Name(s)')
    self.trial_phase = self._table_get_row(table, 'Trial Phase')
    self.short_title = self._table_get_row(table, 'Short Title')
    self.sponsor_name_and_address = self._table_get_row(table, 'Sponsor Name and Address')
    self.sponsor_name, self.sponsor_address = self._sponsor_name_and_address()
    self.regulatory_agency_identifiers = self._table_get_row(table, 'Regulatory Agency Identifier Number(s)')
    self.sponsor_approval_date = self._table_get_row(table, 'Sponsor Approval Date')
    self.study_name = self._study_name()

  def _title_table(self, sections, items):
    for section in sections:
      item = next((x for x in items if x.id == section.contentItemId), None)
      if item:
        soup = self._get_soup(str(item.text))
        for table in soup(['table']):
          title = self._table_get_row(table, 'Full Title')
          if title:
            application_logger.debug(f"Found M11 title page table")
            return table
    application_logger.warning(f"Cannot locate M11 title page table!")
    return None
    
  def _table_get_row(self, table, key: str) -> str:
    if table:
      soup = self._get_soup(str(table))
      for row in soup(['tr']):
        cells = row.findAll('td')
        if str(cells[0].get_text()).upper().startswith(key.upper()):
          application_logger.info(f"Decoded M11 FHIR message {key} = {cells[1].get_text()}")
          return str(cells[1].get_text()).strip()
    return ''

  def _get_soup(self, text):
    soup = None
    try:
      with warnings.catch_warnings(record=True) as warning_list:
        soup =  BeautifulSoup(text, 'html.parser')
      if warning_list:
        for item in warning_list:
          application_logger.debug(f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'")
    except Exception as e:
      application_logger.exception(f"Error raised while Beautiful Soup parsing '{text}'", e)
    return soup
  
  def _study_name(self):
    items = [self.acronym, self.sponsor_protocol_identifier, self.compound_codes]
    for item in items:
      application_logger.debug(f"Study name checking '{item}'")
      if item:
        name = re.sub('[\W_]+', '', item.upper())
        application_logger.info(f"Study name set to '{name}'")
        return name
    return ''  

  def _sponsor_name_and_address(self):
    name = '[Sponsor Name]'
    address = '[Sponsor Address]'
    parts = self.sponsor_name_and_address.split('\n')
    if len(parts) > 0:
      name = parts[0].strip()
      application_logger.info(f"Sponsor name set to '{name}'")
    if len(parts) > 1:
      address = (',').join([x.strip() for x in parts[1:]])
    application_logger.info(f"Sponsor name set to '{name}' with address set to '{address}'")
    return name, address
  