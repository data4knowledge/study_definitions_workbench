from usdm4.api.wrapper import Wrapper
from usdm4.api.study import Study
from usdm4.api.study_design import InterventionalStudyDesign
from usdm4.api.study_version import StudyVersion
from usdm4.api.study_title import StudyTitle
from usdm4.api.study_definition_document import StudyDefinitionDocument
from usdm4.api.study_definition_document_version import StudyDefinitionDocumentVersion
from usdm4.api.population_definition import StudyDesignPopulation
from usdm4.api.eligibility_criterion import (
    EligibilityCriterion,
    EligibilityCriterionItem,
)
from usdm4.api.identifier import StudyIdentifier
from usdm4.api.organization import Organization
from usdm4.api.narrative_content import NarrativeContent, NarrativeContentItem
from usdm4.api.study_amendment import StudyAmendment
from usdm4.api.study_amendment_reason import StudyAmendmentReason
from usdm4.api.endpoint import Endpoint
from usdm4.api.objective import Objective
from usdm4.api.analysis_population import AnalysisPopulation
from usdm4.api.intercurrent_event import IntercurrentEvent
from usdm4.api.study_intervention import StudyIntervention
from usdm4.api.estimand import Estimand
from usdm4.api.governance_date import GovernanceDate
from usdm4.api.geographic_scope import GeographicScope

from usdm_excel.globals import Globals
from uuid import uuid4
from usdm_info import (
    __model_version__ as usdm_version,
)
from d4k_ms_base.logger import application_logger
from app.model.m11_protocol.m11_title_page import M11TitlePage
from app.model.m11_protocol.m11_inclusion_exclusion import M11InclusionExclusion
from app.model.m11_protocol.m11_estimands import M11IEstimands
from app.model.m11_protocol.m11_amendment import M11IAmendment
from app.model.m11_protocol.m11_sections import M11Sections
from app.model.m11_protocol.m11_utility import *
from usdm4.api.address import Address


class M11ToUSDM:
    DIV_OPEN_NS = '<div xmlns="http://www.w3.org/1999/xhtml">'
    DIV_CLOSE = "</div>"

    def __init__(
        self,
        title_page: M11TitlePage,
        inclusion_exclusion: M11InclusionExclusion,
        estimands: M11IEstimands,
        amendment: M11IAmendment,
        sections: M11Sections,
        globals: Globals,
        system_name,
        system_version,
    ):
        self._globals = globals
        self._title_page = title_page
        self._inclusion_exclusion = inclusion_exclusion
        self._estimands = estimands
        self._amendment = amendment
        self._sections = sections
        self._id_manager = self._globals.id_manager
        self._cdisc_ct_library = self._globals.cdisc_ct_library
        self._system_name = system_name
        self._system_version = system_version

    def export(self) -> Wrapper:
        try:
            study = self._study()
            doc_version = self._document_version(study)
            study_version = self._study_version(study)
            # root = model_instance(NarrativeContent, {'name': 'ROOT', 'sectionNumber': '0', 'sectionTitle': 'Root', 'text': '', 'childIds': [], 'previousId': None, 'nextId': None}, self._id_manager)
            # doc_version.contents.append(root)
            local_index = self._section_to_narrative(
                None, 0, 1, doc_version, study_version
            )
            self._double_link(doc_version.contents, "previousId", "nextId")
            return Wrapper(
                study=study,
                usdmVersion=usdm_version,
                systemName=self._system_name,
                systemVersion=self._system_version,
            ).to_json()
        except Exception as e:
            application_logger.exception(
                "Exception raised parsing M11 content. See logs for more details", e
            )
            return None

    def _section_to_narrative(
        self, parent, index, level, doc_version, study_version
    ) -> int:
        process = True
        previous = None
        local_index = index
        loop = 0
        while process:
            section = self._sections.sections[local_index]
            if section.level == level:
                sn = section.number if section.number else ""
                dsn = True if sn else False
                st = section.title if section.title else ""
                dst = True if st else False
                nc_text = f"{self.DIV_OPEN_NS}{section.to_html()}{self.DIV_CLOSE}"
                nci = model_instance(
                    NarrativeContentItem,
                    {"name": f"NCI-{sn}", "text": nc_text},
                    self._id_manager,
                )
                # print(f"NCI: {nci}")
                nc = model_instance(
                    NarrativeContent,
                    {
                        "name": f"NC-{sn}",
                        "sectionNumber": sn,
                        "displaySectionNumber": dsn,
                        "sectionTitle": st,
                        "displaySectionTitle": dst,
                        "contentItemId": nci.id,
                        "childIds": [],
                        "previousId": None,
                        "nextId": None,
                    },
                    self._id_manager,
                )
                doc_version.contents.append(nc)
                study_version.narrativeContentItems.append(nci)
                if parent:
                    parent.childIds.append(nc.id)
                previous = nc
                local_index += 1
            elif section.level > level:
                if previous:
                    local_index = self._section_to_narrative(
                        previous, local_index, level + 1, doc_version, study_version
                    )
                else:
                    application_logger.error("No previous set processing sections")
                    local_index += 1
            elif section.level < level:
                return local_index
            if local_index >= len(self._sections.sections):
                process = False
        return local_index

    def _study(self):
        sponsor_approval_date_code = cdisc_ct_code(
            "C132352", "Sponsor Approval Date", self._cdisc_ct_library, self._id_manager
        )
        protocol_date_code = cdisc_ct_code(
            "C99903x1",
            "Protocol Effective Date",
            self._cdisc_ct_library,
            self._id_manager,
        )
        global_code = cdisc_ct_code(
            "C68846", "Global", self._cdisc_ct_library, self._id_manager
        )
        global_scope = model_instance(
            GeographicScope, {"type": global_code}, self._id_manager
        )
        dates = []
        try:
            approval_date = model_instance(
                GovernanceDate,
                {
                    "name": "Approval Date",
                    "type": sponsor_approval_date_code,
                    "dateValue": self._title_page.sponsor_approval_date,
                    "geographicScopes": [global_scope],
                },
                self._id_manager,
            )
            dates.append(approval_date)
        except:
            application_logger.info(
                f"No document approval date set, source = '{self._title_page.sponsor_approval_date}'"
            )
        try:
            protocol_date = model_instance(
                GovernanceDate,
                {
                    "name": "Protocol Date",
                    "type": protocol_date_code,
                    "dateValue": self._title_page.version_date,
                    "geographicScopes": [global_scope],
                },
                self._id_manager,
            )
            dates.append(protocol_date)
        except:
            application_logger.info(
                f"No document version date set, source = '{self._title_page.version_date}'"
            )
        sponsor_title_code = cdisc_ct_code(
            "C99905x2", "Official Study Title", self._cdisc_ct_library, self._id_manager
        )
        sponsor_short_title_code = cdisc_ct_code(
            "C99905x1", "Brief Study Title", self._cdisc_ct_library, self._id_manager
        )
        acronym_code = cdisc_ct_code(
            "C94108", "Study Acronym", self._cdisc_ct_library, self._id_manager
        )
        protocol_status_code = cdisc_ct_code(
            "C85255", "Draft", self._cdisc_ct_library, self._id_manager
        )
        intervention_model_code = cdisc_ct_code(
            "C82639", "Parallel Study", self._cdisc_ct_library, self._id_manager
        )
        sponsor_code = cdisc_ct_code(
            "C70793", "Clinical Study Sponsor", self._cdisc_ct_library, self._id_manager
        )
        titles = []
        try:
            title = model_instance(
                StudyTitle,
                {"text": self._title_page.full_title, "type": sponsor_title_code},
                self._id_manager,
            )
            titles.append(title)
        except:
            application_logger.info(
                f"No study title set, source = '{self._title_page.full_title}'"
            )
        try:
            title = model_instance(
                StudyTitle,
                {"text": self._title_page.acronym, "type": acronym_code},
                self._id_manager,
            )
            titles.append(title)
        except:
            application_logger.info(
                f"No study acronym set, source = '{self._title_page.acronym}'"
            )
        try:
            title = model_instance(
                StudyTitle,
                {
                    "text": self._title_page.short_title,
                    "type": sponsor_short_title_code,
                },
                self._id_manager,
            )
            titles.append(title)
        except:
            application_logger.info(
                f"No study short title set, source = '{self._title_page.short_title}'"
            )
        protocol_document_version = model_instance(
            StudyDefinitionDocumentVersion,
            {
                "version": self._title_page.version_number,
                "status": protocol_status_code,
            },
            self._id_manager,
        )
        language = language_code("en", "English", self._id_manager)
        doc_type = cdisc_ct_code(
            "C70817", "Protocol", self._cdisc_ct_library, self._id_manager
        )
        protocol_document = model_instance(
            StudyDefinitionDocument,
            {
                "name": "PROTOCOL V1",
                "label": "M11 Protocol",
                "description": "M11 Protocol Document",
                "language": language,
                "type": doc_type,
                "templateName": "M11",
                "versions": [protocol_document_version],
            },
            self._id_manager,
        )
        population, ec_items = self._population()
        objectives, estimands, interventions, analysis_populations = self._objectives()
        study_design = model_instance(
            InterventionalStudyDesign,
            {
                "name": "Study Design",
                "label": "",
                "description": "",
                "rationale": "XXX",
                "model": intervention_model_code,
                "arms": [],
                "studyCells": [],
                "epochs": [],
                "population": population,
                "objectives": objectives,
                "estimands": estimands,
                "studyInterventions": interventions,
                "analysisPopulations": analysis_populations,
                "studyPhase": self._title_page.trial_phase,
            },
            self._id_manager,
        )
        sponsor_address = self._title_page.sponsor_address
        address = model_instance(Address, sponsor_address, self._id_manager)
        address.set_text()
        print(f"ADDRESS: {address}")
        organization = model_instance(
            Organization,
            {
                "name": self._title_page.sponsor_name,
                "type": sponsor_code,
                "identifier": "123456789",
                "identifierScheme": "DUNS",
                "legalAddress": address,
            },
            self._id_manager,
        )
        identifier = model_instance(
            StudyIdentifier,
            {
                "text": self._title_page.sponsor_protocol_identifier,
                "scopeId": organization.id,
            },
            self._id_manager,
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
            "amendments": self._get_amendments(),
            "eligibilityCriterionItems": ec_items,
        }
        study_version = model_instance(StudyVersion, params, self._id_manager)
        study = model_instance(
            Study,
            {
                "id": uuid4(),
                "name": self._title_page.study_name,
                "label": "",
                "description": "",
                "versions": [study_version],
                "documentedBy": [protocol_document],
            },
            self._id_manager,
        )
        return study

    def _objectives(self):
        # print(f"OBJECTIVES")
        objs = []
        ests = []
        treatments = []
        analysis_populations = []
        primary_o = cdisc_ct_code(
            "C85826", "Primary Objective", self._cdisc_ct_library, self._id_manager
        )
        primary_ep = cdisc_ct_code(
            "C94496", "Primary Endpoint", self._cdisc_ct_library, self._id_manager
        )

        int_role = cdisc_ct_code(
            "C41161",
            "Experimental Intervention",
            self._cdisc_ct_library,
            self._id_manager,
        )
        int_type = cdisc_ct_code(
            "C1909", "Pharmacologic Substance", self._cdisc_ct_library, self._id_manager
        )
        int_designation = cdisc_ct_code(
            "C99909x1", "IMP", self._cdisc_ct_library, self._id_manager
        )

        for index, objective in enumerate(self._estimands.objectives):
            # print(f"NEXT OBJECTIVE")
            params = {
                "name": f"Endpoint {index + 1}",
                "text": objective["endpoint"],
                "level": primary_ep,
                "purpose": "",
            }
            ep = model_instance(Endpoint, params, self._id_manager)
            params = {
                "name": f"Objective {index + 1}",
                "text": objective["objective"],
                "level": primary_o,
                "endpoints": [ep],
            }
            obj = model_instance(Objective, params, self._id_manager)
            objs.append(obj)
            params = {
                "name": f"Event {index + 1}",
                "description": objective["i_event"],
                "text": objective["i_event"],
                "strategy": objective["strategy"],
            }
            ie = model_instance(IntercurrentEvent, params, self._id_manager)
            params = {
                "name": f"Analysis Population {index + 1}",
                "text": objective["population"],
            }
            ap = model_instance(AnalysisPopulation, params, self._id_manager)
            analysis_populations.append(ap)
            params = {
                "name": f"Study Intervention {index + 1}",
                "text": objective["treatment"],
                "role": int_role,
                "type": int_type,
                "productDesignation": int_designation,
            }
            treatment = model_instance(StudyIntervention, params, self._id_manager)
            treatments.append(treatment)
            params = {
                "name": f"Estimand {index + 1}",
                "intercurrentEvents": [ie],
                "analysisPopulationId": ap.id,
                "variableOfInterestId": ep.id,
                "interventionIds": [treatment.id],
                "populationSummary": objective["population_summary"],
            }
            est = model_instance(Estimand, params, self._id_manager)
            ests.append(est)
        return objs, ests, treatments, analysis_populations

    def _population(self):
        # print(f"POPULATION")
        results = []
        ec_results = []
        inc = cdisc_ct_code(
            "C25532", "INCLUSION", self._cdisc_ct_library, self._id_manager
        )
        exc = cdisc_ct_code(
            "C25370", "EXCLUSION", self._cdisc_ct_library, self._id_manager
        )
        for index, text in enumerate(self._inclusion_exclusion.inclusion):
            # print(f"INC: {text}")
            params = {
                "name": f"INC{index + 1}",
                "label": f"Inclusion {index + 1} ",
                "description": "",
                "text": text,
            }
            ec_item = model_instance(EligibilityCriterionItem, params, self._id_manager)
            ec_results.append(ec_item)
            params = {
                "name": f"INC{index + 1}",
                "label": f"Inclusion {index + 1} ",
                "description": "",
                "criterionItemId": ec_item.id,
                "category": inc,
                "identifier": f"{index + 1}",
            }
            results.append(
                model_instance(EligibilityCriterion, params, self._id_manager)
            )
        for index, text in enumerate(self._inclusion_exclusion.exclusion):
            # print(f"EXC: {text}")
            params = {
                "name": f"EXC{index + 1}",
                "label": f"Exclusion {index + 1} ",
                "description": "",
                "text": text,
            }
            ec_item = model_instance(EligibilityCriterionItem, params, self._id_manager)
            ec_results.append(ec_item)
            params = {
                "name": f"EXC{index + 1}",
                "label": f"Exclusion {index + 1} ",
                "description": "",
                "criterionItemId": ec_item.id,
                "category": exc,
                "identifier": f"{index + 1}",
            }
            results.append(
                model_instance(EligibilityCriterion, params, self._id_manager)
            )
        params = {
            "name": "STUDY POP",
            "label": "Study Population",
            "description": "",
            "includesHealthySubjects": True,
            "criteria": results,
        }
        return model_instance(
            StudyDesignPopulation, params, self._id_manager
        ), ec_results

    def _get_amendments(self):
        reason = []
        global_code = cdisc_ct_code(
            "C68846", "Global", self._cdisc_ct_library, self._id_manager
        )
        global_scope = model_instance(
            GeographicScope, {"type": global_code}, self._id_manager
        )
        for item in [self._amendment.primary_reason, self._amendment.secondary_reason]:
            params = {"code": item["code"], "otherReason": item["other_reason"]}
            reason.append(
                model_instance(StudyAmendmentReason, params, self._id_manager)
            )
        impact = self._amendment.safety_impact or self._amendment.robustness_impact
        # print(f"IMPACT: {impact}")
        params = {
            "name": "AMENDMENT 1",
            "number": "1",
            "summary": self._amendment.summary,
            "substantialImpact": impact,
            "primaryReason": reason[0],
            "secondaryReasons": [reason[1]],
            "enrollments": [self._amendment.enrollment],
            "geographicScopes": [global_scope],
        }
        return [model_instance(StudyAmendment, params, self._id_manager)]

    def _document_version(self, study: Study) -> StudyDefinitionDocumentVersion:
        return study.documentedBy[0].versions[0]

    def _study_version(self, study: Study) -> StudyDefinitionDocumentVersion:
        return study.versions[0]

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
