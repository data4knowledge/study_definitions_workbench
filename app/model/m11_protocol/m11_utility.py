from app.model.raw_docx.raw_table import RawTable
from usdm_model.code import Code
from usdm_model.alias_code import AliasCode
from usdm_excel.id_manager import IdManager
from usdm_excel.cdisc_ct_library import CDISCCTLibrary
from usdm_excel.iso_3166 import ISO3166
from d4kms_generic import application_logger

def table_get_row(table: RawTable, key: str) -> str:
  for row in table.rows:
    if row.cells[0].is_text():
      if row.cells[0].text().upper().startswith(key.upper()):
        return row.cells[1].text().strip()
  application_logger.info(f"Table row '{key}' not found")
  return ''

def model_instance(cls, params: dict, id_manager: IdManager) -> object:
  params['id'] = params['id'] if 'id' in params else id_manager.build_id(cls)
  params['instanceType'] = cls.__name__
  return cls(**params)

def cdisc_ct_code(code: str, decode: str, ct_library: CDISCCTLibrary, id_manager: IdManager) -> Code:
  return model_instance(Code, {'code': code, 'decode': decode, 'codeSystem': ct_library.system, 'codeSystemVersion': ct_library.version}, id_manager)

def alias_code(standard_code: Code, id_manager: IdManager) -> AliasCode:
  return model_instance(AliasCode, {'standardCode': standard_code}, id_manager)

def iso3166_decode(decode: str, iso_library: ISO3166, id_manager: IdManager) -> Code:
  entry = next((item for item in iso_library.db if item['name'].upper() == decode.upper()), None)
  code = entry['alpha-3'] if entry else 'DNK'
  decode = entry['name']  if entry else 'Denmark'
  return iso_country_code(code, decode, id_manager)

def iso_country_code(code, decode, id_manager: IdManager) -> Code:
  return model_instance(Code, {'code': code, 'decode': decode, 'codeSystem': 'ISO 3166 1 alpha3', 'codeSystemVersion': '2020-08'}, id_manager)
