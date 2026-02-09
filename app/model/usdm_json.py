import json
import yaml
from app.database.file_import import FileImport
from app.model.file_handling.data_files import DataFiles
from usdm4_fhir import M11 as FHIRM11

# from usdm4_fhir import SoA as FHIRSoA
from usdm4_fhir.soa.export.export_soa import ExportSoA as FHIRSoA
from app.database.version import Version
from sqlalchemy.orm import Session
from usdm_model.wrapper import Wrapper
from app.imports.import_manager import ImportManager
from usdm4 import USDM4
from usdm4.api.study import Study
from usdm4.api.study_design import StudyDesign
from usdm4.api.study_version import StudyVersion
from usdm4.api.study_definition_document import (
    StudyDefinitionDocument,
    StudyDefinitionDocumentVersion,
)
from usdm4_cpt.soa.soa import SoA
from usdm4_cpt.document_view.document_view import DocumentView as CPTDocumentView
from usdm4_m11.document_view.document_view import DocumentView as M11DocumentView
from simple_error_log import Errors
from app.utility.soup import get_soup


class USDMJson:
    def __init__(self, id: int, session: Session):  # pragma: no cover
        usdm4 = USDM4()
        self.id = id
        # print(f"ID: {id}")
        version = Version.find(id, session)
        file_import = FileImport.find(version.import_id, session)
        self.uuid = file_import.uuid
        self.type = file_import.type
        self.m11 = (
            True
            if self.type in [ImportManager.M11_DOCX, ImportManager.FHIR_PRISM2_JSON]
            else False
        )
        self._files = DataFiles(file_import.uuid)
        self._data = self._get_usdm()
        errors = Errors()
        self._wrapper: Wrapper = usdm4.loadd(self._data, errors)
        # print(f"USDM JSON DATA: {self._data}")
        self._extra = self._get_extra()

    def fhir(self, version=FHIRM11.PRISM2):
        # print(f"VERSION FHIR: {version}")
        data = self.fhir_data(version)
        fullpath, filename = self._files.save(f"fhir_{version}", data)
        return fullpath, filename, "text/plain"

    def fhir_data(self, version=FHIRM11.PRISM2):
        study: Study = self._wrapper.study
        fhir = FHIRM11()
        data = fhir.to_message(study, self._extra, version)
        return data

    def fhir_soa(self, timeline_id: str):
        data = self.fhir_soa_data(timeline_id)
        fullpath, filename = self._files.save("fhir_soa", data)
        return fullpath, filename, "application/json"

    def fhir_soa_data(self, timeline_id: str):
        study: Study = self._wrapper.study
        fhir = FHIRSoA(study, timeline_id, self.uuid, self._extra)
        return fhir.to_message()

    def json(self):
        fullpath, filename, exists = self._files.path("usdm")
        return fullpath, filename, "application/json"

    # def pdf(self):
    #     usdm = USDMDb()
    #     usdm.from_json(self._data)
    #     data = usdm.to_pdf()
    #     fullpath, filename, exists = self._files.save("protocol", data)
    #     return fullpath, filename, "text/plain"

    def wrapper(self) -> Wrapper:
        return self._wrapper

    def extra(self) -> dict:
        return self._extra

    def study_version(self):
        version = self._data["study"]["versions"][0]
        orgs = {x["id"]: x for x in version["organizations"]}
        result = {
            "id": self.id,
            "version_identifier": version["versionIdentifier"],
            "identifiers": {},
            "titles": {},
            "study_designs": {},
            "phase": "",
        }
        for identifier in version["studyIdentifiers"]:
            org = orgs[identifier["scopeId"]]
            result["identifiers"][org["type"]["code"]] = {
                "label": org["label"] if "label" in org else org["name"],
                "identifier": identifier["text"],
            }
        for title in version["titles"]:
            result["titles"][title["type"]["code"]] = title["text"]
        phases = []
        for design in version["studyDesigns"]:
            result["study_designs"][design["id"]] = {
                "id": design["id"],
                "name": design["name"],
                "label": design["label"] if "label" in design else design["name"],
            }
            phase = design["studyPhase"]["standardCode"]["decode"]
            phases.append(phase)
        result["phase"] = ",".join(phases)
        return result

    def templates(self) -> list[str]:
        study: Study = self._wrapper.study
        return study.document_templates()

    def study_design_overall_parameters(self, id: str):
        version = self._data["study"]["versions"][0]
        design = self._study_design(id)
        if design:
            section = None
            if self.m11:
                section = self._section_by_number("1.1.2")
            if not section:
                section = self._section_by_title_contains("Overall Design")
            text = self._section_item(section) if section else ""
            result = {
                "id": self.id,
                "m11": self.m11,
                "text": text if text else "[Overall Parameters]",
                "intervention_model": None,
                "population_type": None,
                "population_condition": "[Population Condition]",
                "population_age": None,
                "control_type": "[Control Type]",
                "control_description": "[Control Description]",
                "master_protocol": "Yes" if len(version["studyDesigns"]) > 1 else "No",
                "adaptive_design": "No",
                "intervention_method": "[Intervention Assignment Method]",
                "site_distribution": "[Site Distribution and Geographic Scope]",
                "drug_device_indication": "[Drug / Device Combination Product Indication]",
            }
            # result['trial_types'] = self._set_trial_types(id)
            # result['trial_intent'] = self._set_trial_intent_types(id)
            result["intervention_model"] = (
                design["model"]["decode"]
                if design["model"]
                else "[interventional model]"
            )
            result["population_age"] = (
                self._population_age(design)
                if design["population"]
                else self._missing_ages()
            )
            result["population_type"] = (
                "Adult" if result["population_age"]["min"] >= 18 else "Child"
            )
            result["characteristics"] = self._set_characteristics(id)
            if "ADAPTIVE" in result["characteristics"]:
                result["adaptive_design"] = "Yes"
            return result
        else:
            return None

    def study_design_design_parameters(self, id: str):
        design = self._study_design(id)
        if design:
            result = {
                "id": self.id,
                "m11": self.m11,
                "arms": None,
                "trial_blind_scheme": None,
                "blinded_roles": None,
                "participants": None,
                "duration": "[Duration]",
                "independent_committee": "[Independent Committee]",
            }
            result["arms"] = len(design["arms"]) if design["arms"] else "[Arms]"
            result["trial_blind_scheme"] = (
                design["blindingSchema"]["standardCode"]["decode"]
                if ("blindingSchema" in design)
                and design["blindingSchema"]
                and ("standardCode" in design["blindingSchema"])
                else "[Trial Blind Schema]"
            )
            result["blinded_roles"] = self._set_blinded_roles(id)
            result["participants"] = (
                self._population_recruitment(design)
                if design["population"]
                else {"enroll": 0, "complete": 0}
            )
            return result
        else:
            return None

    def study_design_schema(self, id: str):
        design = self._study_design(id)
        if design:
            section = None
            if self.m11:
                section = self._section_by_number("1.2")
            if not section:
                section = self._section_by_title_contains("trial schema")
            if not section:
                section = self._section_by_title_contains("study design")
            text = self._section_item(section) if section else "[Study Design]"
            image = self._image_in_section(section) if section else "[Study Design]"
            return {"id": self.id, "m11": self.m11, "image": image, "text": text}
        else:
            return None

    def study_design_interventions(self, id: str):
        design = self._study_design(id)
        if design:
            section = None
            if self.m11:
                section = self._section_by_number("6.1")
            if not section:
                section = self._section_by_title_contains("Trial Intervention")
            if not section:
                section = self._section_by_title_contains("Intervention")
            text = self._section_item(section) if section else ""
            result = {
                "id": self.id,
                "m11": self.m11,
                "interventions": [],
                "text": text if text else "[Trial Interventions]",
            }
            if "studyInterventionIds" in design:
                for int_id in design["studyInterventionIds"]:
                    intervention = self._find_intervention(
                        self._data["study"]["versions"][0], int_id
                    )
                    # print(f"R1:")
                    record = {}
                    record["arm"] = self._arm_from_intervention(
                        design, intervention["id"]
                    )
                    record["intervention"] = intervention
                    result["interventions"].append(record)
            # print(f"INTERVENTIONS: {result}")
            return result
        else:
            return None

    def _find_intervention(self, version: dict, id: str) -> dict:
        return next((x for x in version["studyInterventions"] if x["id"] == id), None)

    def study_design_estimands(self, id: str):
        version = self._data["study"]["versions"][0]
        design = self._study_design(id)
        # print(f"ESTIMANDS: {'design' if design else ''}")
        if design:
            section = None
            if self.m11:
                section = self._section_by_number("3.1")
            if not section:
                section = self._section_by_title_contains("Primary Objective")
            text = self._section_item(section) if section else ""
            result = {
                "id": self.id,
                "m11": self.m11,
                "estimands": [],
                "text": text if text else "[Estimands]",
            }
            if "estimands" in design:
                for estimand in design["estimands"]:
                    record = {}
                    # print(f"R1:")
                    record["treatment"] = self._intervention(
                        version, estimand["interventionIds"]
                    )
                    record["summary_measure"] = estimand["populationSummary"]
                    record["analysis_population"] = estimand["analysisPopulationId"]
                    record["intercurrent_events"] = estimand["intercurrentEvents"]
                    record["objective"], record["endpoint"] = (
                        self._objective_endpoint_from_estimand(
                            design, estimand["variableOfInterestId"]
                        )
                    )
                    result["estimands"].append(record)
            # print(f"ESTIMANDS: {result}")
            return result
        else:
            return None

    def schedule_of_activities(self, id: str):
        errors = Errors()
        study: Study
        version: StudyVersion
        design: StudyDesign
        study, version, design = self._wrapper.study_version_and_design(id)
        if study and version and design:
            soas = []
            documents = version.documents(study.document_map())
            for doc_info in documents:
                dv = None
                doc: StudyDefinitionDocument = doc_info["document"]
                doc_version: StudyDefinitionDocumentVersion = doc_info["version"]
                # print(f"TEMPLATE: {doc.templateName}")
                if doc.templateName.upper() == "CPT":
                    dv = CPTDocumentView(version, doc_version, errors)
                elif doc.templateName.upper() == "M11":
                    dv = M11DocumentView(version, doc_version, errors)
                if dv:
                    soas.append(
                        {
                            "template": doc.templateName,
                            "soa": dv.schedule_of_activities(),
                        }
                    )
            # print(f"SoAs: {len(soas)}")
            return {
                "id": self.id,
                "study_id": design.id,
                "data": [x.model_dump() for x in design.scheduleTimelines],
                "documents": soas,
            }
        return {"id": self.id, "study_id": design.id, "data": [], "document": []}

    def soa(self, study_id: str, id: str):
        wrapper = self.wrapper()
        version = wrapper.study.first_version()
        if version:
            design = version.find_study_design(study_id)
            if design:
                timeline = design.find_timeline(id)
                if timeline:
                    result = {
                        "id": self.id,
                        "study_id": design.id,
                        "m11": self.m11,
                        "timeline": dict(timeline),
                        "soa": SoA().to_html(version, design, timeline),
                    }
                    return result
        return None

    def sample_size(self, id: str) -> dict:
        return self._section_response(id, "10.11", "sample size", "[Sample Size]")

    def analysis_sets(self, id: str) -> dict:
        return self._section_response(id, "10.2", "analysis sets", "[Analysis Sets]")

    def analysis_objectives(self, id: str) -> dict:
        return self._section_response(
            id,
            "10.4",
            "analysis associated with primary",
            "[Analysis Associated with the Primary Objectives]",
        )

    def adverse_events_special_interest(self, id: str) -> dict:
        return self._section_response(
            id,
            "9.3.2",
            "adverse events of special interest",
            "[Adverse Events of Special Interest]",
        )

    def safety_assessments(self, id: str) -> dict:
        return self._section_response(
            id,
            "8.4",
            "safety assessments and procedures",
            "[Safety Assessment and Procedures]",
        )

    def protocol_sections_list(self):
        sections = self.protocol_sections()
        result = []
        for section in sections:
            if (
                section["sectionNumber"] and section["sectionNumber"] != "0"
            ) and section["sectionTitle"]:
                result.append(
                    {
                        "section_number": section["sectionNumber"],
                        "section_title": section["sectionTitle"],
                    }
                )
        return result

    def protocol_sections(self):
        document = self._document()
        if document:
            sections = []
            narrative_content = self._first_narrative_content(document)
            while narrative_content:
                sections.append(narrative_content)
                narrative_content = self._find_narrative_content(
                    document, narrative_content["nextId"]
                )
            return sections
        return None

    def section(self, id):
        document = self._document()
        _ = self._data["study"]["versions"][0]
        if document:
            narrative_content = self._find_narrative_content(document, id)
            narrative_content["heading"], narrative_content["level"] = (
                self._format_heading(narrative_content)
            )
            narrative_content["text"] = self._section_item(narrative_content)
            return narrative_content
        return None

    def _section_item(self, narrative_content: dict) -> str:
        version = self._data["study"]["versions"][0]
        return next(
            (
                x["text"]
                for x in version["narrativeContentItems"]
                if x["id"] == narrative_content["contentItemId"]
            ),
            "",
        )

    def _section_response(self, id: str, number: str, title: str, default: str) -> dict:
        design = self._study_design(id)
        if design and self.m11:
            return {
                "id": self.id,
                "m11": self.m11,
                "text": self._section_full_text(number, title, default),
            }
        return None

    def _section_full_text(self, number: str, title: str, default: str) -> str:
        section = None
        document = self._document()
        if document:
            section = self._section_by_number(number)
            if not section:
                section = self._section_by_title_contains(title)
            if section:
                text = []
                process = True
                top_level = self._get_level(section)
                while process:
                    # print(f"SECTION: {section}")
                    heading, level = self._format_heading(section)
                    text.append(heading)
                    text.append(self._section_item(section))
                    section = self._find_narrative_content(document, section["nextId"])
                    process = True if self._get_level(section) > top_level else False
        return ("").join(text) if section else default

    def _get_number(self, narrative_content: dict):
        try:
            return int(narrative_content["sectionNumber"])
        except Exception:
            return 0

    def _get_level(self, narrative_content: dict):
        section_number = narrative_content["sectionNumber"]
        if section_number is None:
            result = 1
        elif section_number.lower().startswith("appendix"):
            result = 1
        else:
            text = (
                section_number[:-1] if section_number.endswith(".") else section_number
            )
            result = len(text.split("."))
        return result

    def _format_heading(self, narrative_content):
        level = self._get_level(narrative_content)
        number = narrative_content["sectionNumber"]
        title = narrative_content["sectionTitle"]
        if number and number == "0":
            return "", level
        elif number and title:
            return f"<h{level}>{number} {title}</h{level}>", level
        elif number:
            return f"<h{level}>{number}</h{level}>", level
        elif title:
            return f"<h{level}>{title}</h{level}>", level
        else:
            return "", level

    def _first_narrative_content(self, document: dict) -> dict:
        return next(
            (x for x in document["contents"] if not x["previousId"] and x["nextId"]),
            None,
        )

    def _find_narrative_content(self, document: dict, id: str) -> dict:
        return next((x for x in document["contents"] if x["id"] == id), None)

    def _intervention(self, study_version: dict, intervention_ids: list) -> dict:
        if len(intervention_ids) == 0:
            return None
        intervention_id = intervention_ids[0]
        return next(
            (
                x
                for x in study_version["studyInterventions"]
                if x["id"] == intervention_id
            ),
            None,
        )

    def _objective_endpoint_from_estimand(
        self, study_design: dict, variable_of_interest_id: str
    ) -> dict:
        for objective in study_design["objectives"]:
            endpoint = self._endpoint_from_objective(objective, variable_of_interest_id)
            if endpoint:
                return objective, endpoint
        return None, None

    def _endpoint_from_objective(self, objective: list, endpoint_id: str) -> dict:
        return next((x for x in objective["endpoints"] if x["id"] == endpoint_id), None)

    def _arm_from_intervention(self, study_design: dict, intervention_id: str) -> dict:
        version = self._data["study"]["versions"][0]
        element = next(
            (x for x in version["studyInterventions"] if x["id"] == intervention_id),
            None,
        )
        if element:
            cell = next(
                (
                    x
                    for x in study_design["studyCells"]
                    if intervention_id in x["elementIds"]
                ),
                None,
            )
            if cell:
                return next(
                    (x for x in study_design["arms"] if x["id"] == cell["id"]), None
                )
        return {"label": "[Not Found]", "type": {"decode": "[Not Found]"}}

    def _set_blinded_roles(self, id) -> dict:
        _ = self._study_design(id)
        result = {}
        # if design['maskingRoles']:
        #   for item in design['maskingRoles']:
        #     result[item['role']['decode']] = item['role']['decode']
        # else:
        #   result['[Blinded Roles]'] = '[Blinded Roles]'
        return result

    def _set_characteristics(self, id) -> dict:
        return self._set_multiple(id, "characteristics", "[Characteristics]")

    def _set_trial_intent_types(self, id) -> dict:
        return self._set_multiple(id, "trialIntentTypes", "[Trial Intent]")

    def _set_trial_types(self, id) -> dict:
        return self._set_multiple(id, "trialTypes", "[Trial TYpes]")

    def _set_multiple(self, id: str, collection: str, missing: str) -> dict:
        design = self._study_design(id)
        result = {}
        if collection in design:
            for item in design[collection]:
                result[item["decode"]] = item["decode"]
        else:
            result[missing] = missing
        return result

    def _image_in_section(self, section):
        text = self._section_item(section) if section else ""
        soup = get_soup(text)
        for ref in soup(["img"]):
            return ref
        return ""

    def _section_by_number(self, number) -> dict:
        document = self._document()
        if document:
            return next(
                (
                    x
                    for x in document["contents"]
                    if x["sectionNumber"] is not None and x["sectionNumber"] == number
                ),
                None,
            )
        return None

    def _section_by_title_contains(self, title) -> dict:
        document = self._document()
        if document:
            return next(
                (
                    x
                    for x in document["contents"]
                    if x["sectionTitle"] is not None
                    and title.upper() in x["sectionTitle"].upper()
                ),
                None,
            )
        return None

    def _study_design(self, id: str) -> dict:
        version = self._data["study"]["versions"][0]
        return next((x for x in version["studyDesigns"] if x["id"] == id), None)

    def _document(self) -> dict:
        try:
            version = self._data["study"]["versions"][0]
            id = version["documentVersionIds"][0]
            return next(
                (
                    x
                    for x in self._data["study"]["documentedBy"][0]["versions"]
                    if x["id"] == id
                ),
                None,
            )
        except Exception:
            return None

    # def _get_soup(self, text: str):
    #     try:
    #         with warnings.catch_warnings(record=True) as warning_list:
    #             result = BeautifulSoup(text, "html.parser")
    #         if warning_list:
    #             pass
    #             # for item in warning_list:
    #             #  errors_and_logging.debug(f"Warning raised within Soup package, processing '{text}'\nMessage returned '{item.message}'")
    #         return result
    #     except Exception:
    #         # errors_and_logging.exception(f"Parsing '{text}' with soup", e)
    #         return None

    def _population_age(self, study_design: dict) -> dict:
        try:
            population = study_design["population"]
            result = self._min_max(population["plannedAge"])
            for cohort in population["cohorts"]:
                cohort = self._min_max(population["plannedAge"])
                if cohort["min"] < result["min"]:
                    result["min"] = cohort["min"]  # pragma: no cover
                if cohort["max"] > result["max"]:
                    result["max"] = cohort["max"]  # pragma: no cover
            return result
        except Exception:
            return self._missing_ages()

    def _min_max(self, item) -> dict:
        # print(f"ITEM: {item}")
        return (
            {
                "min": int(item["minValue"]["value"]),
                "min_unit": item["minValue"]["unit"]["standardCode"]["decode"],
                "max": int(item["maxValue"]["value"]),
                "max_unit": item["maxValue"]["unit"]["standardCode"]["decode"],
            }
            if item
            else self._missing_ages()
        )

    def _missing_ages(self):
        return {"min": 0, "max": 0, "min_unit": "", "max_unit": ""}

    def _population_recruitment(self, study_design: dict) -> dict:
        try:
            population = study_design["population"]
            enroll = self._range_or_quantity(population, "plannedEnrollmentNumber")
            complete = self._range_or_quantity(population, "plannedCompletionNumber")
            # print(f"ENORLL: {enroll}, {complete}")
            return {"enroll": int(enroll), "complete": int(complete)}
        except Exception:
            return {"enroll": "[Enrolled]", "complete": "[Complete]"}

    def _range_or_quantity(seæf, data: dict, attribute_name: dict) -> dict:
        quanity_name = f"{attribute_name}Quantity"
        range_name = f"{attribute_name}Range"
        if data[quanity_name]:
            return data[quanity_name]["value"]
        if data[range_name]:
            return data[range_name]["maxValue"]
        return "0"

    def _get_usdm(self):
        fullpath, filename, exists = self._files.path("usdm")
        data = open(fullpath)
        return json.load(data)

    def _get_raw(self):
        fullpath, filename, exists = self._files.path("usdm")
        f = open(fullpath)
        return f.read()

    def _get_extra(self):
        fullpath, filename, exists = self._files.path("extra")
        data = open(fullpath)
        return yaml.load(data, Loader=yaml.FullLoader)
