from usdm_model.wrapper import Wrapper
from usdm4.api.study import *
from usdm4.api.study_version import *


class USDMM11TitlePage:
    def __init__(self, wrapper: Wrapper, extra: dict):
        # print(f"EXTRA: {extra}")
        title_page = extra["title_page"]
        misc = extra["miscellaneous"]
        amendment = extra["amendment"]
        study_version = wrapper.study.first_version()
        self.sponosr_confidentiality = title_page["sponsor_confidentiality"]
        self.acronym = study_version.acronym_text()
        self.full_title = study_version.official_title_text()
        self.sponsor_protocol_identifier = study_version.sponsor_identifier_text()
        self.original_protocol = title_page["original_protocol"]
        self.version_number = study_version.versionIdentifier
        self.version_date = study_version.protocol_date_value()
        self.amendment_identifier = title_page["amendment_identifier"]
        self.amendment_scope = title_page["amendment_scope"]
        self.amendment_details = title_page["amendment_details"]
        self.compound_codes = title_page["compound_codes"]
        self.compound_names = title_page["compound_names"]
        self.trial_phase = ", ".join(
            [x.studyPhase.standardCode.decode for x in study_version.studyDesigns]
        )
        self.short_title = study_version.short_title_text()
        self.sponsor_name = study_version.sponsor_name()
        self.sponsor_address = study_version.sponsor_address()
        self.regulatory_agency_identifiers = title_page["regulatory_agency_identifiers"]
        self.sponsor_approval_date = study_version.approval_date_value()
        self.manufacturer_name_and_address = title_page["manufacturer_name_and_address"]
        self.sponsor_signatory = title_page["sponsor_signatory"]
        self.medical_expert_contact = misc["medical_expert_contact"]
        self.sae_reporting_method = misc["sae_reporting_method"]
