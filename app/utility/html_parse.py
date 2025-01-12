import warnings
from bs4 import BeautifulSoup
from d4kms_generic import application_logger


class M11HTML:
    def __init__(self, text: str):
        self._soup = self._get_soup(text)

    def title_page(self):
        tables = self._soup(["table"])
        if tables:
            table = tables[0]
            # print(f"TABLE: {table}")
            self.full_title = self._table_get_row(table, "Full Title")
            self.acronym = self._table_get_row(table, "Acronym")
            self.sponsor_protocol_identifier = self._table_get_row(
                table, "Sponsor Protocol Identifier"
            )
            self.original_protocol = self._table_get_row(table, "Original Protocol")
            self.version_number = self._table_get_row(table, "Version Number")
            self.amendment_identifier = self._table_get_row(
                table, "Amendment Identifier"
            )
            self.amendment_scope = self._table_get_row(table, "Amendment Scope")
            self.compound_codes = self._table_get_row(table, "Compound Code(s)")
            self.compund_names = self._table_get_row(table, "Compound Name(s)")
            self.trial_phase_raw = self._table_get_row(table, "Trial Phase")
            # self.trial_phase = self._phase()
            self.short_title = self._table_get_row(table, "Short Title")
            self.sponsor_name_and_address = self._table_get_row(
                table, "Sponsor Name and Address"
            )
            # self.sponsor_name, self.sponsor_address = self._sponsor_name_and_address()
            self.regulatory_agency_identifiers = self._table_get_row(
                table, "Regulatory Agency Identifier Number(s)"
            )
            self.sponsor_approval_date = self._table_get_row(
                table, "Sponsor Approval Date"
            )

    def _table_get_row(self, table, key: str) -> str:
        # print(f"TGR: {type(table)}")
        soup = self._soup(str(table))
        for row in soup(["tr"]):
            cells = row.find("td")
            if str(cells[0]).upper().startswith(key.upper()):
                return str(cells[1]).strip()
        return "[Not Found]"

    def _get_soup(self, text):
        soup = None
        try:
            with warnings.catch_warnings(record=True) as warning_list:
                soup = BeautifulSoup(text, "html.parser")
            if warning_list:
                for item in warning_list:
                    application_logger.debug(
                        f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'"
                    )
        except Exception as e:
            application_logger.exception(
                f"Eerror raised while Beautiful Soup parsing '{text}'", e
            )
        return soup
