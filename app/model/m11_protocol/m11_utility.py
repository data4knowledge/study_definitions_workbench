from app.model.raw_docx.raw_table import RawTable
from usdm4.api.code import Code
from usdm4.api.alias_code import AliasCode
from usdm_excel.id_manager import IdManager
from usdm_excel.cdisc_ct_library import CDISCCTLibrary
from usdm_excel.iso_3166 import ISO3166
from d4k_ms_base.logger import application_logger


def text_within(this_text, in_text):
    return this_text.upper() in in_text.upper()


def table_get_row(table: RawTable, key: str) -> str:
    for row in table.rows:
        if row.cells[0].is_text():
            # if row.cells[0].text().upper().startswith(key.upper()):
            if text_within(key, row.cells[0].text()):
                cell = row.next_cell(0)
                result = cell.text() if cell else ""
                application_logger.debug(f"Table find for '{key}' = '{result}'")
                return result
    application_logger.debug(f"Table find for '{key}' failed")
    return ""


def table_get_row_html(table: RawTable, key: str) -> str:
    for row in table.rows:
        if row.cells[0].is_text():
            # if row.cells[0].text().upper().startswith(key.upper()):
            if text_within(key, row.cells[0].text()):
                cell = row.next_cell(0)
                return cell.to_html() if cell else ""
    return ""


def model_instance(cls, params: dict, id_manager: IdManager) -> object:
    try:
        params["id"] = params["id"] if "id" in params else id_manager.build_id(cls)
        params["instanceType"] = cls.__name__
        return cls(**params)
    except Exception as e:
        application_logger.exception(
            f"Failed to create model instance of class {cls}\nparams: {params}\n Exception: {e.errors()}",
            e,
        )
        raise


def cdisc_ct_code(
    code: str, decode: str, ct_library: CDISCCTLibrary, id_manager: IdManager
) -> Code:
    return model_instance(
        Code,
        {
            "code": code,
            "decode": decode,
            "codeSystem": ct_library.system,
            "codeSystemVersion": ct_library.version,
        },
        id_manager,
    )


def alias_code(standard_code: Code, id_manager: IdManager) -> AliasCode:
    return model_instance(AliasCode, {"standardCode": standard_code}, id_manager)


def iso3166_decode(decode: str, iso_library: ISO3166, id_manager: IdManager) -> Code:
    for key in ["name", "alpha-2", "alpha-3"]:
        entry = next(
            (item for item in iso_library.db if item[key].upper() == decode.upper()),
            None,
        )
        if entry:
            application_logger.info(f"ISO3166 decode of '{decode}' to {entry}")
            break
    return (
        iso_country_code(entry["alpha-3"], entry["name"], id_manager) if entry else None
    )


def iso_country_code(code, decode, id_manager: IdManager) -> Code:
    return model_instance(
        Code,
        {
            "code": code,
            "decode": decode,
            "codeSystem": "ISO 3166 1 alpha3",
            "codeSystemVersion": "2020-08",
        },
        id_manager,
    )


def language_code(code: str, decode: str, id_manager: IdManager) -> Code:
    return model_instance(
        Code,
        {
            "code": code,
            "decode": decode,
            "codeSystem": "ISO 639-1",
            "codeSystemVersion": "2002",
        },
        id_manager,
    )
