from usdm4.api.wrapper import Wrapper
from usdm4.api.study import Study
from usdm4.api.study_design import InterventionalStudyDesign
from usdm4.api.study_version import StudyVersion
from usdm4.api.study_title import StudyTitle
from usdm4.api.study_definition_document import StudyDefinitionDocument
from usdm4.api.study_definition_document_version import StudyDefinitionDocumentVersion
from usdm4.api.code import Code
from usdm4.api.alias_code import AliasCode
from usdm4.api.identifier import StudyIdentifier
from usdm4.api.organization import Organization
from usdm4.api.narrative_content import NarrativeContent, NarrativeContentItem
from usdm4.api.governance_date import GovernanceDate
from usdm4.api.geographic_scope import GeographicScope
from usdm4.api.address import Address
from usdm4.api.population_definition import StudyDesignPopulation
from fhir.resources.bundle import Bundle
from fhir.resources.composition import CompositionSection
from usdm_info import (
    __model_version__ as usdm_version,
)
from app import SYSTEM_NAME, VERSION
from app.model.file_handling.data_files import DataFiles
from app.usdm.fhir.fhir_title_page import FHIRTitlePage
from d4k_ms_base.logger import application_logger
from app.model.m11_protocol.m11_utility import language_code
from usdm_excel.iso_3166 import ISO3166
from usdm_excel.globals import Globals


class FromFHIRV1:
    class LogicError(Exception):
        pass

    def __init__(self, uuid: str):
        self._globals = Globals()
        self._globals.create()
        self._errors_and_logging = self._globals.errors_and_logging
        self._id_manager = self._globals.id_manager
        self._iso = ISO3166(self._globals)
        self._cdisc_ct_manager = self._globals.cdisc_ct_library
        self._uuid = uuid
        self._ncs = []
        self._title_page = None

    async def to_usdm(self) -> str:
        try:
            files = DataFiles(self._uuid)
            data = files.read("fhir")
            study = await self._from_fhir(self._uuid, data)
            return Wrapper(
                study=study,
                usdmVersion=usdm_version,
                systemName=SYSTEM_NAME,
                systemVersion=VERSION,
            ).to_json()
        except Exception as e:
            self._errors_and_logging.exception(
                "Exception raised parsing FHIR content. See logs for more details", e
            )
            return None

    def extra(self):
        return {
            "title_page": self._title_page.extra(),
            "amendment": {
                "amendment_details": "",
                "robustness_impact": False,
                "robustness_impact_reason": "",
                "safety_impact": False,
                "safety_impact_reason": "",
            },
            "miscellaneous": {
                "medical_expert_contact": "",
                "sae_reporting_method": "",
                "sponsor_signatory": "",
            },
        }

    async def _from_fhir(self, uuid: str, data: str) -> Wrapper:
        bundle = Bundle.parse_raw(data)
        protocol_document, ncis = self._document(bundle)
        study = await self._study(protocol_document, ncis)
        return study

    def _document(self, bundle):
        self._ncs = []
        protocl_status_code = self._cdisc_ct_code("C85255", "Draft")
        protocl_document_version = self._model_instance(
            StudyDefinitionDocumentVersion,
            {"version": "1", "status": protocl_status_code},
        )
        language = language_code("en", "English", self._id_manager)
        doc_type = self._cdisc_ct_code("C70817", "Protocol")
        protocl_document = self._model_instance(
            StudyDefinitionDocument,
            {
                "name": "PROTOCOL V1",
                "label": "M11 Protocol",
                "description": "M11 Protocol Document",
                "language": language,
                "type": doc_type,
                "templateName": "M11",
                "versions": [protocl_document_version],
            },
        )
        # root = self._model_instance(NarrativeContent, {'name': 'ROOT', 'sectionNumber': '0', 'sectionTitle': 'Root', 'text': '', 'childIds': [], 'previousId': None, 'nextId': None})
        # protocl_document_version.contents.append(root)
        ncis = []
        for item in bundle.entry[0].resource.section:
            nc = self._section(item, protocl_document_version, ncis, 0)
        self._double_link(protocl_document_version.contents, "previousId", "nextId")
        # print(f"DOC: {protocl_document}")
        return protocl_document, ncis

    def _section(
        self,
        section: CompositionSection,
        protocol_document_version: StudyDefinitionDocumentVersion,
        ncis: list,
        index: int,
    ):
        index = index + 1
        # print(f"SECTION: {section.title}, {section.code.text}")
        section_number = self._get_section_number(section.code.text)
        section_title = section.title
        sn = section_number if section_number else ""
        dsn = True if sn else False
        st = section_title if section_title else ""
        dst = True if st else False
        # print(f"SECTION: sn='{sn}', dsn='{dsn}', st='{st}', dst='{dst}'")
        text = section.text.div if section.text else "&nbsp"
        nci = self._model_instance(
            NarrativeContentItem, {"name": f"NCI-{index}", "text": text}
        )
        nc = self._model_instance(
            NarrativeContent,
            {
                "name": f"NC-{index}",
                "sectionNumber": sn,
                "displaySectionNumber": dsn,
                "sectionTitle": st,
                "displaySectionTitle": dst,
                "contentItemId": nci.id,
                "childIds": [],
                "previousId": None,
                "nextId": None,
            },
        )
        protocol_document_version.contents.append(nc)
        ncis.append(nci)
        if section.section:
            for item in section.section:
                child_nc = self._section(item, protocol_document_version, ncis, index)
                nc.childIds.append(child_nc.id)
        return nc

    def _get_section_number(self, text):
        parts = text.split("-")
        return parts[0].replace("section", "") if len(parts) >= 2 else ""

    async def _study(self, protocol_document: StudyDefinitionDocument, ncis: list):
        protocol_document_version = protocol_document.versions[0]
        sections = protocol_document_version.contents
        self._title_page = FHIRTitlePage(sections, ncis)
        await self._title_page.process()

        # Dates
        sponsor_approval_date_code = self._cdisc_ct_code(
            "C132352", "Sponsor Approval Date"
        )
        protocol_date_code = self._cdisc_ct_code("C99903x1", "Protocol Effective Date")
        global_code = self._cdisc_ct_code("C68846", "Global")
        global_scope = self._model_instance(GeographicScope, {"type": global_code})
        dates = []
        try:
            approval_date = self._model_instance(
                GovernanceDate,
                {
                    "name": "Approval Date",
                    "type": sponsor_approval_date_code,
                    "dateValue": self._title_page.sponsor_approval_date,
                    "geographicScopes": [global_scope],
                },
            )
            dates.append(approval_date)
        except:
            application_logger.info(
                f"No document approval date set, source = '{self._title_page.sponsor_approval_date}'"
            )
        try:
            protocol_date = self._model_instance(
                GovernanceDate,
                {
                    "name": "Protocol Date",
                    "type": protocol_date_code,
                    "dateValue": self._title_page.version_date,
                    "geographicScopes": [global_scope],
                },
            )
            dates.append(protocol_date)
        except:
            application_logger.info(
                f"No document version date set, source = '{self._title_page.version_date}'"
            )

        # Titles
        sponsor_title_code = self._cdisc_ct_code("C99905x2", "Official Study Title")
        sponsor_short_title_code = self._cdisc_ct_code("C99905x1", "Brief Study Title")
        acronym_code = self._cdisc_ct_code("C94108", "Study Acronym")
        titles = []
        try:
            title = self._model_instance(
                StudyTitle,
                {"text": self._title_page.full_title, "type": sponsor_title_code},
            )
            titles.append(title)
        except:
            application_logger.info(
                f"No study title set, source = '{self._title_page.full_title}'"
            )
        try:
            title = self._model_instance(
                StudyTitle, {"text": self._title_page.acronym, "type": acronym_code}
            )
            titles.append(title)
        except:
            application_logger.info(
                f"No study acronym set, source = '{self._title_page.acronym}'"
            )
        try:
            title = self._model_instance(
                StudyTitle,
                {
                    "text": self._title_page.short_title,
                    "type": sponsor_short_title_code,
                },
            )
            titles.append(title)
        except:
            application_logger.info(
                f"No study short title set, source = '{self._title_page.short_title}'"
            )

        # Build
        intervention_model_code = self._cdisc_ct_code("C82639", "Parallel Study")
        sponsor_code = self._cdisc_ct_code("C70793", "Clinical Study Sponsor")
        empty_population = self._model_instance(
            StudyDesignPopulation,
            {
                "name": "Study Design Population",
                "label": "Study Population",
                "description": "Empty population details",
                "includesHealthySubjects": True,
            },
        )
        study_design = self._model_instance(
            InterventionalStudyDesign,
            {
                "name": "Study Design",
                "label": "",
                "description": "",
                "rationale": "[Not Found]",
                "model": intervention_model_code,
                "arms": [],
                "studyCells": [],
                "epochs": [],
                "population": empty_population,
                "studyPhase": self._phase(self._title_page.trial_phase),
            },
        )
        self._title_page.sponsor_address["country"] = self._iso3166_decode(
            self._title_page.sponsor_address["country"].upper()
        )
        address = self._model_instance(Address, self._title_page.sponsor_address)
        address.set_text()
        organization = self._model_instance(
            Organization,
            {
                "name": self._title_page.sponsor_name,
                "type": sponsor_code,
                "identifier": "123456789",
                "identifierScheme": "DUNS",
                "legalAddress": address,
            },
        )
        identifier = self._model_instance(
            StudyIdentifier,
            {
                "text": self._title_page.sponsor_protocol_identifier,
                "scopeId": organization.id,
            },
        )
        params = {
            "versionIdentifier": self._title_page.version_number,
            "rationale": "XXX",
            "titles": titles,
            "dateValues": dates,
            "studyDesigns": [study_design],
            "documentVersionIds": [protocol_document_version.id],
            "studyIdentifiers": [identifier],
            "organizations": [organization],
            "narrativeContentItems": ncis,
        }
        study_version = self._model_instance(StudyVersion, params)
        study = self._model_instance(
            Study,
            {
                "id": self._uuid,
                "name": self._title_page.study_name,
                "label": self._title_page.study_name,
                "description": f"FHIR Imported {self._title_page.study_name}",
                "versions": [study_version],
                "documentedBy": [protocol_document],
            },
        )
        return study

    def _cdisc_ct_code(self, code, decode):
        return self._model_instance(
            Code,
            {
                "code": code,
                "decode": decode,
                "codeSystem": self._cdisc_ct_manager.system,
                "codeSystemVersion": self._cdisc_ct_manager.version,
            },
        )

    def _iso3166_decode(self, decode: str) -> Code:
        for key in ["name", "alpha-2", "alpha-3"]:
            entry = next(
                (item for item in self._iso.db if item[key].upper() == decode.upper()),
                None,
            )
            if entry:
                application_logger.info(f"ISO3166 decode of '{decode}' to {entry}")
                break
        return (
            self._iso_country_code(entry["alpha-3"], entry["name"]) if entry else None
        )

    def _iso_country_code(self, code, decode):
        return self._model_instance(
            Code,
            {
                "code": code,
                "decode": decode,
                "codeSystem": "ISO 3166 1 alpha3",
                "codeSystemVersion": "2020-08",
            },
        )

    def _document_version(self, study):
        return study.documentedBy.versions[0]

    def _model_instance(self, cls, params):
        try:
            params["id"] = (
                params["id"] if "id" in params else self._id_manager.build_id(cls)
            )
            params["instanceType"] = cls.__name__
            return cls(**params)
        except Exception as e:
            application_logger.exception(
                f"Failed to create model instance of class {cls}\nparams: {params}\n Exception: {e.errors()}",
                e,
            )
            raise

    def _double_link(self, items, prev, next):
        for idx, item in enumerate(items):
            if idx == 0:
                setattr(item, prev, None)
            else:
                the_id = getattr(items[idx - 1], "id")
                setattr(item, prev, the_id)
            if idx == len(items) - 1:
                setattr(item, next, None)
            else:
                the_id = getattr(items[idx + 1], "id")
                setattr(item, next, the_id)

    def _phase(self, raw_phase):
        phase_map = [
            (
                ["0", "PRE-CLINICAL", "PRE CLINICAL"],
                {"code": "C54721", "decode": "Phase 0 Trial"},
            ),
            (["1", "I"], {"code": "C15600", "decode": "Phase I Trial"}),
            (["1-2"], {"code": "C15693", "decode": "Phase I/II Trial"}),
            (["1/2"], {"code": "C15693", "decode": "Phase I/II Trial"}),
            (["1/2/3"], {"code": "C198366", "decode": "Phase I/II/III Trial"}),
            (["1/3"], {"code": "C198367", "decode": "Phase I/III Trial"}),
            (["1A", "IA"], {"code": "C199990", "decode": "Phase Ia Trial"}),
            (["1B", "IB"], {"code": "C199989", "decode": "Phase Ib Trial"}),
            (["2", "II"], {"code": "C15601", "decode": "Phase II Trial"}),
            (["2-3", "II-III"], {"code": "C15694", "decode": "Phase II/III Trial"}),
            (["2A", "IIA"], {"code": "C49686", "decode": "Phase IIa Trial"}),
            (["2B", "IIB"], {"code": "C49688", "decode": "Phase IIb Trial"}),
            (["3", "III"], {"code": "C15602", "decode": "Phase III Trial"}),
            (["3A", "IIIA"], {"code": "C49687", "decode": "Phase IIIa Trial"}),
            (["3B", "IIIB"], {"code": "C49689", "decode": "Phase IIIb Trial"}),
            (["4", "IV"], {"code": "C15603", "decode": "Phase IV Trial"}),
            (["5", "V"], {"code": "C47865", "decode": "Phase V Trial"}),
        ]
        phase = raw_phase.upper().replace("PHASE", "").strip()
        for tuple in phase_map:
            if phase in tuple[0]:
                entry = tuple[1]
                cdisc_phase_code = self._cdisc_ct_code(entry["code"], entry["decode"])
                application_logger.info(
                    f"Trial phase '{phase}' decoded as '{entry['code']}', '{entry['decode']}'"
                )
                return self._model_instance(
                    AliasCode, {"standardCode": cdisc_phase_code}
                )
        cdisc_phase_code = self._cdisc_ct_code("C48660", "[Trial Phase] Not Applicable")
        application_logger.warning(f"Trial phase '{phase}' not decoded")
        return self._model_instance(AliasCode, {"standardCode": cdisc_phase_code})
