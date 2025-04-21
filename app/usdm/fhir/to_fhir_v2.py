import warnings
import datetime
from uuid import uuid4
from bs4 import BeautifulSoup
from app.usdm.fhir.to_fhir import ToFHIR
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.identifier import Identifier as FHIRIdentifier
from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.extension import Extension
from fhir.resources.researchstudy import ResearchStudyAssociatedParty
from fhir.resources.researchstudy import ResearchStudyProgressStatus
from fhir.resources.organization import Organization as FHIROrganization
from fhir.resources.fhirtypes import ResearchStudyLabelType, AddressType
from fhir.resources.group import Group
from d4k_ms_base.logger import application_logger
from usdm4.api.code import Code as USDMCode
from usdm4.api.endpoint import Endpoint as USDMEndpoint
from usdm4.api.study_intervention import StudyIntervention as USDMStudyIntervention
from usdm4.api.governance_date import GovernanceDate as USDMGovernanceDate
from usdm4.api.organization import Organization as USDMOrganization
from usdm4.api.address import Address as USDMAddress
from usdm4.api.study_version import StudyVersion as USDMStudyVersion
from usdm4.api.study_design import StudyDesign as USDMStudyDesign
from usdm4.api.eligibility_criterion import EligibilityCriterion
from usdm4.api.study_version import *
from usdm4.api.identifier import *


class ToFHIRV2(ToFHIR):
    class LogicError(Exception):
        pass

    def to_fhir(self) -> None:
        try:
            self._entries = []
            sections = []
            root = self.protocol_document_version.contents[0]
            # print(f"ROOT: {root}")
            for id in root.childIds:
                content = next(
                    (x for x in self.protocol_document_version.contents if x.id == id),
                    None,
                )
                section = self._content_to_section(content)
                if section:
                    sections.append(section)
            type_code = CodeableConcept(text="EvidenceReport")
            date = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            author = Reference(display="USDM")
            self._entries.append(
                {
                    "item": Composition(
                        title=self.doc_title,
                        type=type_code,
                        section=sections,
                        date=date,
                        status="preliminary",
                        author=[author],
                    ),
                    "url": "https://www.example.com/Composition/1234B",
                }
            )
            ie = self._inclusion_exclusion_critieria()
            rs = self._research_study(ie.id)
            self._entries.append(
                {"item": rs, "url": "https://www.example.com/Composition/1234A"}
            )
            self._entries.append(
                {"item": ie, "url": "https://www.example.com/Composition/1234X1"}
            )
            identifier = FHIRIdentifier(
                system="urn:ietf:rfc:3986", value=f"urn:uuid:{self._uuid}"
            )
            entries = []
            for entry in self._entries:
                entries.append(
                    BundleEntry(resource=entry["item"], fullUrl=entry["url"])
                )
            bundle = Bundle(
                id=None,
                entry=entries,
                type="document",
                identifier=identifier,
                timestamp=date,
            )
            return bundle.json()
        except Exception as e:
            self._errors_and_logging.exception(
                "Exception raised generating FHIR content. See logs for more details",
                e,
            )
            return None

    def _inclusion_exclusion_critieria(self):
        version = self.study_version
        design = self.study_design
        criteria = design.criterion_map()
        all_of = self._extension_string(
            "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.combinationMethod",
            "all-of",
        )
        group = Group(
            id=str(uuid4()),
            characteristic=[],
            type="person",
            membership="definitional",
            extension=[all_of],
        )
        for index, id in enumerate(design.population.criterionIds):
            criterion = criteria[id]
            self._criterion(criterion, group.characteristic)
        return group

    def _criterion(self, criterion: EligibilityCriterion, collection: list):
        version = self.study_version
        code = CodeableConcept(
            extension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                    "valueCode": "not-applicable",
                }
            ]
        )
        value = CodeableConcept(
            extension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                    "valueCode": "not-applicable",
                }
            ]
        )
        # ext = self._extension_markdown('http://hl7.org/fhir/StructureDefinition/rendering-markdown', criterion.text)
        # if ext:
        #   outer = self._extension_markdown_wrapper_2('http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.characteristic.description', 'Not filled', ext)
        #   exclude = True if criterion.category.code == 'C25370' else False
        #   collection.append({'extension': outer, 'code': code, 'valueCodeableConcept': value, 'exclude': exclude})

        criterion_item = version.criterion_item(criterion.criterionItemId)
        if criterion_item:
            soup = self._get_soup(criterion_item.text)
            cleaned_text = soup.get_text()

            outer = self._extension_markdown_wrapper_2(
                "http://hl7.org/fhir/6.0/StructureDefinition/extension-Group.characteristic.description",
                cleaned_text,
                None,
            )
            exclude = True if criterion.category.code == "C25370" else False
            collection.append(
                {
                    "extension": outer,
                    "code": code,
                    "valueCodeableConcept": value,
                    "exclude": exclude,
                }
            )

    def _research_study(self, group_id: str) -> ResearchStudy:
        version = self.study_version
        organizations = version.organization_map()
        result = ResearchStudy(
            status="draft",
            identifier=[],
            extension=[],
            label=[],
            associatedParty=[],
            progressStatus=[],
            objective=[],
            comparisonGroup=[],
            outcomeMeasure=[],
        )

        # Sponsor Confidentiality Statememt
        ext = self._extension_string(
            "http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement",
            self._title_page["sponsor_confidentiality"],
        )
        if ext:
            result.extension.append(ext)

        # Full Title
        result.title = self._get_title("Official Study Title").text

        # Trial Acronym
        acronym = self._get_title("Study Acronym")
        if acronym:
            type = CodeableConcept(coding=[self._coding_from_code(acronym.type)])
            result.label.append(ResearchStudyLabelType(type=type, value=acronym.text))

        # Sponsor Protocol Identifier
        for identifier in version.studyIdentifiers:
            org = identifier.scoped_by(organizations)
            identifier_code = CodeableConcept(text=f"{org.type.decode}")
            # print(f"IDENTIFIER: {identifier} = {identifier_code}")
            result.identifier.append(
                {
                    "type": identifier_code,
                    "system": "https://example.org/sponsor-identifier",
                    "value": identifier.text,
                }
            )

        # Original Protocol - No implementation details currently
        x = self._title_page["original_protocol"]

        # Version Number
        result.version = version.versionIdentifier

        # Version Date
        approval_date = self._document_date()
        if approval_date:
            result.date = approval_date.dateValue

        # Amendment Identifier
        identifier_code = CodeableConcept(text=f"{'Amendment Identifier'}")
        result.identifier.append(
            {
                "type": identifier_code,
                "system": "https://example.org/amendment-identifier",
                "value": self._title_page["amendment_identifier"],
            }
        )

        # Amendment Scope - Part of Amendment

        # Compound Codes - No implementation details currently
        x = self._title_page["compound_codes"]

        # Compound Names - No implementation details currently
        x = self._title_page["compound_names"]

        # Trial Phase
        phase = self._phase()
        phase_code = Coding(
            system=phase.codeSystem,
            version=phase.codeSystemVersion,
            code=phase.code,
            display=phase.decode,
        )
        result.phase = CodeableConcept(coding=[phase_code], text=phase.decode)

        # Short Title
        title = self._get_title("Brief Study Title")
        if title:
            type = CodeableConcept(coding=[self._coding_from_code(title.type)])
            result.label.append(ResearchStudyLabelType(type=type, value=title.text))

        # Sponsor Name and Address
        sponsor = version.sponsor()
        org = self._organization_from_organization(sponsor)
        if org:
            self._entries.append(
                {"item": org, "url": "https://www.example.com/Composition/1234D"}
            )
            item = self._associated_party_reference(
                f"Organization/{self._fix_id(org.id)}", "sponsor", "sponsor"
            )
            if item:
                result.associatedParty.append(item)

        # Manufacturer Name and Address
        x = self._title_page["manufacturer_name_and_address"]

        # Regulatory Agency Identifiers, see above
        x = self._title_page["regulatory_agency_identifiers"]

        # Sponsor Approval
        status = self._progress_status(
            self._title_page["sponsor_approval_date"],
            "sponsor-approved",
            "sponsor apporval date",
        )
        if status:
            result.progressStatus.append(status)

        # Sponsor Signatory
        item = self._associated_party(
            self._title_page["sponsor_signatory"],
            "sponsor-signatory",
            "sponsor signatory",
        )
        if item:
            result.associatedParty.append(item)

        # Medical Expert Contact
        item = self._associated_party(
            self._title_page["medical_expert_contact"],
            "medical-expert",
            "medical expert",
        )
        if item:
            result.associatedParty.append(item)

        # SAE Reporting Method
        ext = self._extension_string(
            "http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sae-reporting-method",
            self._title_page["sae_reporting_method"],
        )
        if ext:
            result.extension.append(ext)

        # Amendment
        ext = self._amendment_ext(version)
        if ext:
            result.extension.append(ext)

        # Objectives
        self._estimands(result)

        # Recruitment
        self._recruitment(result, group_id)

        # print(f"RESEARCH STUDY: {result}")
        return result

    def _recruitment(self, research_study: ResearchStudy, group_id):
        research_study.recruitment = {"eligibility": {"reference": f"Group/{group_id}"}}

    def _estimands(self, research_study: ResearchStudy):
        version = self.study_version
        design = version.studyDesigns[0]
        for objective in self._primary_objectives():
            try:
                ext = self._extension_wrapper(
                    "http://example.org/fhir/extension/estimand"
                )
                id = self._treatment(research_study, objective["treatment"])
                pls_ext = self._extension_id(
                    "populationLevelSummary", self._fix_id(objective["summary"].id)
                )
                if pls_ext:
                    ext.extension.append(pls_ext)
                id = self._endpoint(research_study, objective["endpoint"])
                pls_ext = self._extension_id("endpoint-outcomeMeasure", id)
                if pls_ext:
                    ext.extension.append(pls_ext)
                pls_ext = self._extension_codeable_text(
                    "populationLevelSummary", objective["summary"].populationSummary
                )
                if pls_ext:
                    ext.extension.append(pls_ext)
                for ice in objective["events"]:
                    event_ext = self._extension_codeable_text("event", ice.description)
                    strategy_ext = self._extension_codeable_text("event", ice.strategy)
                    ice_ext = self._extension_wrapper("intercurrentEvent")
                    if ice_ext:
                        ice_ext.extension.append(event_ext)
                        ice_ext.extension.append(strategy_ext)
                item = {
                    "type": {"coding": self._coding_from_code(objective["type"])},
                    "description": objective["objective"].description,
                    "extension": [ext],
                }
                research_study.objective.append(item)
            except Exception as e:
                application_logger.exception("Exception in method _estimands", e)

    def _treatment(
        self, research_study: ResearchStudy, treatment: USDMStudyIntervention
    ):
        id = treatment.id
        item = {
            "linkId": self._fix_id(id),
            "name": "Treatment Group",
            "intendedExposure": {"display": treatment.description},
            "observedGroup": {"display": "Not Availabe"},
        }
        research_study.comparisonGroup.append(item)
        return id

    def _endpoint(self, research_study: ResearchStudy, endpoint: USDMEndpoint):
        id = endpoint.id
        item = {
            "extension": [
                {
                    "url": "http://example.org/fhir/extension/linkId",
                    "valueId": self._fix_id(id),
                }
            ],
            "name": "Endpoint",
            "description": endpoint.text,
        }
        research_study.outcomeMeasure.append(item)
        return id

    # def _sponsor_identifier(self):
    #   for identifier in self.study_version.studyIdentifiers:
    #     if identifier.studyIdentifierScope.organizationType.code == 'C70793':
    #       return identifier
    #   return None

    # def _sponsor(self):
    #   for identifier in self.study_version.studyIdentifiers:
    #     if identifier.studyIdentifierScope.organizationType.code == 'C70793':
    #       return identifier.studyIdentifierScope
    #   return None

    def _phase(self):
        return self.study_design.studyPhase.standardCode

    def _document_date(self) -> USDMGovernanceDate:
        dates = self.study_version.dateValues
        for date in dates:
            if date.type.code == "C99903x1":
                return date
        return None

    def _primary_objectives(self) -> list:
        return self._objective("C85826")

    def _objective(self, type_code) -> list:
        results = []
        version = self.study_version
        design = version.studyDesigns[0]
        for objective in design.objectives:
            if objective.level.code == type_code:
                endpoint = objective.endpoints[0]  # Assuming only one for estimands?
                result = {
                    "objective": objective,
                    "type": objective.level,
                    "endpoint": objective.endpoints[0],
                }
                estimand = self._estimand_for(design, endpoint)
                if estimand:
                    result["population"] = self.study_design.find_analysis_population(
                        estimand.analysisPopulationId
                    )
                    # print(f"ESTIMAND ID: {estimand.interventionId}")
                    intervention = self.study_version.intervention(
                        estimand.interventionIds[0]
                    )
                    result["treatment"] = intervention if intervention else None
                    result["summary"] = estimand
                    result["events"] = []
                    for event in estimand.intercurrentEvents:
                        result["events"].append(event)
                # print(f"OBJECIVE: {result}")
                results.append(result)
        # print(f"OBJECIVE: {results[0].keys()}")
        return results

    def _estimand_for(self, design: USDMStudyDesign, endpoint: USDMEndpoint):
        return next(
            (x for x in design.estimands if x.variableOfInterestId == endpoint.id), None
        )

    def _coding_from_code(self, code: USDMCode):
        return Coding(
            system=code.codeSystem,
            version=code.codeSystemVersion,
            code=code.code,
            display=code.decode,
        )

    def _codeable_concept(self, code: Coding):
        return CodeableConcept(coding=[code])

    def _organization_from_organization(self, organization: USDMOrganization):
        # print(f"ORG: {organization}")
        address = self._address_from_address(organization.legalAddress)
        name = organization.label if organization.label else organization.name
        return FHIROrganization(
            id=str(uuid4()), name=name, contact=[{"address": address}]
        )

    def _address_from_address(self, address: USDMAddress):
        x = dict(address)
        x.pop("instanceType")
        y = {}
        for k, v in x.items():
            if v:
                y[k] = v
        if "lines" in y:
            y["line"] = y["lines"]
            y.pop("lines")
        if "country" in y:
            y["country"] = address.country.decode
        result = AddressType(y)
        # print(f"ADDRESS: {result}")
        return result

    def _associated_party(self, value: str, role_code: str, role_display: str):
        if value:
            code = Coding(
                system="http://hl7.org/fhir/research-study-party-role",
                code=role_code,
                display=role_display,
            )
            role = CodeableConcept(coding=[code])
            return ResearchStudyAssociatedParty(role=role, party={"display": value})
        else:
            return None

    def _associated_party_reference(
        self, reference: str, role_code: str, role_display: str
    ):
        if reference:
            code = Coding(
                system="http://hl7.org/fhir/research-study-party-role",
                code=role_code,
                display=role_display,
            )
            role = CodeableConcept(coding=[code])
            return ResearchStudyAssociatedParty(
                role=role, party={"reference": reference}
            )
        else:
            return None

    def _progress_status(self, value: str, state_code: str, state_display: str):
        # print(f"DATE: {value}")
        if value:
            code = Coding(
                system="http://hl7.org/fhir/research-study-party-role",
                code=state_code,
                display=state_display,
            )
            state = CodeableConcept(coding=[code])
            return ResearchStudyProgressStatus(state=state, period={"start": value})
        else:
            return None

    def _amendment_ext(self, version: USDMStudyVersion):
        if len(version.amendments) == 0:
            return None
        source = version.amendments[0]
        amendment = Extension(
            url="http://example.org/fhir/extension/studyAmendment", extension=[]
        )
        ext = self._extension_string(
            "amendmentNumber", value=self._title_page["amendment_identifier"]
        )
        if ext:
            amendment.extension.append(ext)
        ext = self._extension_string("scope", value=self._title_page["amendment_scope"])
        if ext:
            amendment.extension.append(ext)
        ext = self._extension_string(
            "details", value=self._title_page["amendment_details"]
        )
        if ext:
            amendment.extension.append(ext)
        ext = self._extension_boolean(
            "substantialImpactSafety", value=self._amendment["safety_impact"]
        )
        if ext:
            amendment.extension.append(ext)
        ext = self._extension_string(
            "substantialImpactSafety", value=self._amendment["safety_impact_reason"]
        )
        if ext:
            amendment.extension.append(ext)
        ext = self._extension_boolean(
            "substantialImpactSafety", value=self._amendment["robustness_impact"]
        )
        if ext:
            amendment.extension.append(ext)
        ext = self._extension_string(
            "substantialImpactSafety", value=self._amendment["robustness_impact_reason"]
        )
        if ext:
            amendment.extension.append(ext)

        primary = self._codeable_concept(
            self._coding_from_code(source.primaryReason.code)
        )
        ext = self._extension_codeable(
            "http://hl7.org/fhir/uv/ebm/StructureDefinition/primaryReason",
            value=primary,
        )
        if ext:
            amendment.extension.append(ext)
            secondary = self._codeable_concept(
                self._coding_from_code(source.secondaryReasons[0].code)
            )
            ext = self._extension_codeable(
                "http://hl7.org/fhir/uv/ebm/StructureDefinition/secondaryReason",
                value=secondary,
            )
            if ext:
                amendment.extension.append(ext)
        return amendment

    def _extension_wrapper(self, url):
        return Extension(url=url, extension=[])

    def _extension_string(self, url: str, value: str):
        return Extension(url=url, valueString=value) if value else None

    def _extension_boolean(self, url: str, value: str):
        return Extension(url=url, valueBoolean=value) if value else None

    def _extension_codeable(self, url: str, value: CodeableConcept):
        return Extension(url=url, valueCodeableConcept=value) if value else None

    def _extension_codeable_text(self, url: str, value: str):
        return Extension(url=url, valueString=value) if value else None

    def _extension_markdown_wrapper(self, url, value, ext):
        return Extension(url=url, extension=[ext]) if value else None

    def _extension_markdown_wrapper_2(self, url, value, ext):
        return Extension(url=url, valueString=value)

    def _extension_markdown(self, url, value):
        return Extension(url=url, valueMarkdown=value) if value else None

    def _extension_id(self, url: str, value: str):
        value = self._fix_id(value)
        return Extension(url=url, valueId=value) if value else None

    def _fix_id(self, value: str) -> str:
        return value.replace("_", "-")

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
