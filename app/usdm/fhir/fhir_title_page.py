import re
import warnings
import dateutil.parser as parser
from bs4 import BeautifulSoup
from d4k_ms_base.logger import application_logger
from app.utility.address_service import AddressService


class FHIRTitlePage:
    def __init__(self, sections: list, items: list):
        self._sections = sections
        self._items = items
        self._address_service = AddressService()
        self.sponosr_confidentiality = None
        self.full_title = None
        self.acronym = None
        self.sponsor_protocol_identifier = None
        self.original_protocol = None
        self.version_number = None
        self.version_date = None
        self.amendment_identifier = None
        self.amendment_scope = None
        self.amendment_details = None
        self.trial_phase_raw = None
        self.compound_codes = None
        self.compound_names = None
        self.trial_phase = None
        self.short_title = None
        self.sponsor_name_and_address = None
        self.sponsor_name = None
        self.sponsor_address = None
        self.regulatory_agency_identifiers = None
        self.sponsor_approval_date = None
        self.manufacturer_name_and_address = None
        self.sponsor_signatory = None
        self.medical_expert_contact = None
        self.sae_reporting_method = None
        self.study_name = None

    async def process(self):
        table = self._title_table(self._sections, self._items)
        self.sponosr_confidentiality = self._table_get_row(
            table, "Sponsor Confidentiality"
        )
        self.full_title = self._table_get_row(table, "Full Title")
        self.acronym = self._table_get_row(table, "Acronym")
        self.sponsor_protocol_identifier = self._table_get_row(
            table, "Sponsor Protocol Identifier"
        )
        self.original_protocol = self._table_get_row(table, "Original Protocol")
        self.version_number = self._table_get_row(table, "Version Number")
        self.version_date = self._get_protocol_date(table)
        self.amendment_identifier = self._table_get_row(table, "Amendment Identifier")
        self.amendment_scope = self._table_get_row(table, "Amendment Scope")
        self.amendment_details = self._table_get_row(table, "Amendment Details")
        self.trial_phase_raw = self._table_get_row(table, "Trial Phase")
        self.compound_codes = self._table_get_row(table, "Compound Code")
        self.compound_names = self._table_get_row(table, "Compound Name")
        self.trial_phase = self._table_get_row(table, "Trial Phase")
        self.short_title = self._table_get_row(table, "Short Title")
        self.sponsor_name_and_address = self._table_get_row(
            table, "Sponsor Name and Address"
        )
        self.sponsor_name, self.sponsor_address = await self._sponsor_name_and_address()
        self.regulatory_agency_identifiers = self._table_get_row(
            table, "Regulatory Agency Identifier Number(s)"
        )
        self.sponsor_approval_date = self._get_sponsor_approval_date(table)
        self.manufacturer_name_and_address = self._table_get_row(table, "Manufacturer")
        self.sponsor_signatory = self._table_get_row(table, "Sponsor Signatory")
        self.medical_expert_contact = self._table_get_row(table, "Medical Expert")
        self.sae_reporting_method = self._table_get_row(table, "SAE Reporting")
        self.study_name = self._study_name()

    def extra(self):
        return {
            "sponsor_confidentiality": self.sponosr_confidentiality,
            "compound_codes": self.compound_codes,
            "compound_names": self.compound_names,
            "amendment_identifier": self.amendment_identifier,
            "amendment_scope": self.amendment_scope,
            "amendment_details": self.amendment_details,
            "sponsor_name_and_address": self.sponsor_name_and_address,
            "original_protocol": self.original_protocol,
            "regulatory_agency_identifiers": self.regulatory_agency_identifiers,
            "manufacturer_name_and_address": self.manufacturer_name_and_address,
            "sponsor_signatory": self.sponsor_signatory,
            "medical_expert_contact": self.medical_expert_contact,
            "sae_reporting_method": self.sae_reporting_method,
            "sponsor_approval_date": self.sponsor_approval_date,
        }

    def _title_table(self, sections, items):
        for section in sections:
            item = next((x for x in items if x.id == section.contentItemId), None)
            if item:
                soup = self._get_soup(str(item.text))
                for table in soup(["table"]):
                    title = self._table_get_row(table, "Full Title")
                    if title:
                        application_logger.debug("Found M11 title page table")
                        # print(f"TABLE: {table}")
                        return table
        application_logger.warning("Cannot locate M11 title page table!")
        return None

    def _table_get_row(self, table, key: str) -> str:
        if table:
            soup = self._get_soup(str(table))
            for row in soup(["tr"]):
                cells = row.findAll("td")
                if key.upper() in str(cells[0].get_text()).upper():
                    r1 = [x.get_text() for x in cells[1](["p"])]
                    r2 = ("\n").join(r1)
                    application_logger.info(f"Decoded M11 FHIR message {key} = {r2}")
                    return r2
        application_logger.info(f"Failed to decode M11 FHIR message {key}")
        return ""

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
                f"Error raised while Beautiful Soup parsing '{text}'", e
            )
        return soup

    def _study_name(self):
        items = [self.acronym, self.sponsor_protocol_identifier, self.compound_codes]
        for item in items:
            application_logger.debug(f"Study name checking '{item}'")
            if item:
                name = re.sub(r"[\W_]+", "", item.upper())
                application_logger.info(f"Study name set to '{name}'")
                return name
        return ""

    async def _sponsor_name_and_address(self):
        name = "[Sponsor Name]"
        parts = self.sponsor_name_and_address.split("\n")
        params = {
            "line": "",
            "city": "",
            "district": "",
            "state": "",
            "postalCode": "",
            "country": "",
        }
        if len(parts) > 0:
            name = parts[0].strip()
            application_logger.info(f"Sponsor name set to '{name}'")
        if len(parts) > 1:
            application_logger.info(
                f"Processing address {self.sponsor_name_and_address}"
            )
            tmp_address = (" ").join([x.strip() for x in parts[1:]])
            results = await self._address_service.parser(tmp_address)
            application_logger.info(
                f"Address service result '{tmp_address}' returned {results}"
            )
            if "error" in results:
                application_logger.error(
                    f"Error with address server: {results['error']}"
                )
            else:
                for result in results:
                    if result["label"] == "country":
                        params["country"] = self._preserve_original(
                            parts[1:], result["value"]
                        )
                    elif result["label"] == "postcode":
                        params["postalCode"] = self._preserve_original(
                            parts[1:], result["value"]
                        )
                    elif result["label"] in ["city", "state"]:
                        params[result["label"]] = self._preserve_original(
                            parts[1:], result["value"]
                        )
        application_logger.info(f"Name and address result '{name}', '{params}'")
        return name, params

    def _get_sponsor_approval_date(self, table):
        return self._get_date(table, "Sponsor Approval")

    def _get_protocol_date(self, table):
        return self._get_date(table, "Version Date")

    def _get_date(self, table, text):
        try:
            date_text = self._table_get_row(table, text)
            if date_text:
                date = parser.parse(date_text)
                return date
            else:
                return None
        except Exception as e:
            application_logger.exception(
                f"Exception raised during date processing for '{text}'", e
            )
            return None

    def _preserve_original(self, original_parts, value):
        for part in original_parts:
            for item in re.split(r"[,\s]+", part):
                if item.upper() == value.upper():
                    print(f"PRESERVE: {value} as {item}")
                    return item
        return value
