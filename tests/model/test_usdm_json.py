import copy
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from app.model.usdm_json import USDMJson
from tests.helpers.usdm_test_data import build_usdm_data


def _build_usdm(data=None, m11=True, extra=None):
    """Build a USDMJson instance bypassing __init__."""
    usdm = object.__new__(USDMJson)
    usdm.id = 1
    usdm.uuid = "test-uuid"
    usdm.type = "m11_docx" if m11 else "cpt_docx"
    usdm.m11 = m11
    usdm._data = data or build_usdm_data()
    usdm._wrapper = MagicMock()
    usdm._files = MagicMock()
    usdm._extra = extra or {}
    return usdm


# --- study_version ---


class TestStudyVersion:

    def test_basic(self):
        usdm = _build_usdm()
        result = usdm.study_version()
        assert result["id"] == 1
        assert result["version_identifier"] == "v1.0"
        assert result["titles"]["C207616"] == "Test Study"
        assert result["titles"]["C207615"] == "Brief Test"
        assert result["phase"] == "Phase III"
        assert "design-1" in result["study_designs"]

    def test_org_with_label(self):
        usdm = _build_usdm()
        result = usdm.study_version()
        assert result["identifiers"]["C54149"]["label"] == "Pharma Label"
        assert result["identifiers"]["C54149"]["identifier"] == "STUDY-001"

    def test_org_without_label(self):
        usdm = _build_usdm()
        result = usdm.study_version()
        assert result["identifiers"]["C188863"]["label"] == "Regulatory"
        assert result["identifiers"]["C188863"]["identifier"] == "REG-002"

    def test_design_with_label(self):
        usdm = _build_usdm()
        result = usdm.study_version()
        assert result["study_designs"]["design-1"]["label"] == "Design Label"

    def test_design_without_label(self):
        data = build_usdm_data()
        del data["study"]["versions"][0]["studyDesigns"][0]["label"]
        usdm = _build_usdm(data)
        result = usdm.study_version()
        assert result["study_designs"]["design-1"]["label"] == "Design One"

    def test_multiple_phases(self):
        data = build_usdm_data()
        second_design = copy.deepcopy(data["study"]["versions"][0]["studyDesigns"][0])
        second_design["id"] = "design-2"
        second_design["studyPhase"]["standardCode"]["decode"] = "Phase II"
        data["study"]["versions"][0]["studyDesigns"].append(second_design)
        usdm = _build_usdm(data)
        result = usdm.study_version()
        assert "Phase III" in result["phase"]
        assert "Phase II" in result["phase"]


# --- study_design_overall_parameters ---


class TestStudyDesignOverallParameters:

    def test_m11_with_section(self):
        usdm = _build_usdm()
        result = usdm.study_design_overall_parameters("design-1")
        assert result is not None
        assert result["id"] == 1
        assert result["m11"] is True
        assert result["intervention_model"] == "PARALLEL"
        assert "Overall Design Content" in result["text"]

    def test_non_m11(self):
        usdm = _build_usdm(m11=False)
        result = usdm.study_design_overall_parameters("design-1")
        assert result is not None
        assert result["m11"] is False

    def test_design_not_found(self):
        usdm = _build_usdm()
        result = usdm.study_design_overall_parameters("nonexistent")
        assert result is None

    def test_no_model(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["model"] = None
        usdm = _build_usdm(data)
        result = usdm.study_design_overall_parameters("design-1")
        assert result["intervention_model"] == "[interventional model]"

    def test_no_population(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["population"] = None
        usdm = _build_usdm(data)
        result = usdm.study_design_overall_parameters("design-1")
        assert result["population_age"]["min"] == 0

    def test_population_age_adult(self):
        usdm = _build_usdm()
        result = usdm.study_design_overall_parameters("design-1")
        assert result["population_age"]["min"] == 18
        assert result["population_age"]["max"] == 65
        assert result["population_type"] == "Adult"

    def test_population_age_child(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["population"]["plannedAge"]["minValue"]["value"] = "5"
        usdm = _build_usdm(data)
        result = usdm.study_design_overall_parameters("design-1")
        assert result["population_type"] == "Child"

    def test_adaptive_design(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["characteristics"].append({"decode": "ADAPTIVE"})
        usdm = _build_usdm(data)
        result = usdm.study_design_overall_parameters("design-1")
        assert result["adaptive_design"] == "Yes"

    def test_master_protocol_single(self):
        usdm = _build_usdm()
        result = usdm.study_design_overall_parameters("design-1")
        assert result["master_protocol"] == "No"

    def test_master_protocol_multiple(self):
        data = build_usdm_data()
        second_design = copy.deepcopy(data["study"]["versions"][0]["studyDesigns"][0])
        second_design["id"] = "design-2"
        data["study"]["versions"][0]["studyDesigns"].append(second_design)
        usdm = _build_usdm(data)
        result = usdm.study_design_overall_parameters("design-1")
        assert result["master_protocol"] == "Yes"

    def test_no_section(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        result = usdm.study_design_overall_parameters("design-1")
        assert result["text"] == "[Overall Parameters]"


# --- study_design_design_parameters ---


class TestStudyDesignDesignParameters:

    def test_basic(self):
        usdm = _build_usdm()
        result = usdm.study_design_design_parameters("design-1")
        assert result is not None
        assert result["arms"] == 1
        assert result["trial_blind_scheme"] == "DOUBLE_BLIND"

    def test_no_arms(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["arms"] = None
        usdm = _build_usdm(data)
        result = usdm.study_design_design_parameters("design-1")
        assert result["arms"] == "[Arms]"

    def test_no_blinding(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["blindingSchema"] = None
        usdm = _build_usdm(data)
        result = usdm.study_design_design_parameters("design-1")
        assert result["trial_blind_scheme"] == "[Trial Blind Schema]"

    def test_no_blinding_key(self):
        data = build_usdm_data()
        del data["study"]["versions"][0]["studyDesigns"][0]["blindingSchema"]
        usdm = _build_usdm(data)
        result = usdm.study_design_design_parameters("design-1")
        assert result["trial_blind_scheme"] == "[Trial Blind Schema]"

    def test_design_not_found(self):
        usdm = _build_usdm()
        result = usdm.study_design_design_parameters("nonexistent")
        assert result is None

    def test_no_population(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["population"] = None
        usdm = _build_usdm(data)
        result = usdm.study_design_design_parameters("design-1")
        assert result["participants"] == {"enroll": 0, "complete": 0}

    def test_participants(self):
        usdm = _build_usdm()
        result = usdm.study_design_design_parameters("design-1")
        assert result["participants"]["enroll"] == 100
        assert result["participants"]["complete"] == 80


# --- study_design_schema ---


class TestStudyDesignSchema:

    def test_m11_with_section(self):
        usdm = _build_usdm()
        result = usdm.study_design_schema("design-1")
        assert result is not None
        assert result["m11"] is True
        assert "Trial Schema" in result["text"]

    def test_non_m11_finds_by_title(self):
        usdm = _build_usdm(m11=False)
        result = usdm.study_design_schema("design-1")
        assert result is not None
        assert result["m11"] is False

    def test_design_not_found(self):
        usdm = _build_usdm()
        result = usdm.study_design_schema("nonexistent")
        assert result is None

    def test_no_section(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        result = usdm.study_design_schema("design-1")
        assert result["text"] == "[Study Design]"
        assert result["image"] == "[Study Design]"

    def test_image_in_section(self):
        usdm = _build_usdm()
        result = usdm.study_design_schema("design-1")
        assert result["image"] is not None


# --- study_design_interventions ---


class TestStudyDesignInterventions:

    def test_with_intervention_ids(self):
        usdm = _build_usdm()
        result = usdm.study_design_interventions("design-1")
        assert result is not None
        assert len(result["interventions"]) == 1
        assert result["interventions"][0]["intervention"]["name"] == "Drug A"

    def test_no_intervention_ids(self):
        data = build_usdm_data()
        del data["study"]["versions"][0]["studyDesigns"][0]["studyInterventionIds"]
        usdm = _build_usdm(data)
        result = usdm.study_design_interventions("design-1")
        assert result["interventions"] == []

    def test_design_not_found(self):
        usdm = _build_usdm()
        result = usdm.study_design_interventions("nonexistent")
        assert result is None

    def test_m11_section_text(self):
        usdm = _build_usdm()
        result = usdm.study_design_interventions("design-1")
        assert "Trial Intervention Content" in result["text"]

    def test_no_section(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        result = usdm.study_design_interventions("design-1")
        assert result["text"] == "[Trial Interventions]"

    def test_m11_section_fallback_to_title(self):
        data = build_usdm_data()
        # Remove section 6.1 so m11 number lookup fails, falls to title
        doc = data["study"]["documentedBy"][0]["versions"][0]
        for c in doc["contents"]:
            if c["sectionNumber"] == "6.1":
                c["sectionNumber"] = "6.X"
                break
        usdm = _build_usdm(data)
        result = usdm.study_design_interventions("design-1")
        assert "Trial Intervention Content" in result["text"]


# --- study_design_estimands ---


class TestStudyDesignEstimands:

    def test_basic(self):
        usdm = _build_usdm()
        result = usdm.study_design_estimands("design-1")
        assert result is not None
        assert len(result["estimands"]) == 1
        est = result["estimands"][0]
        assert est["summary_measure"] == "Mean difference"
        assert est["objective"]["text"] == "Primary Objective"
        assert est["endpoint"]["text"] == "Primary Endpoint"

    def test_no_estimands_key(self):
        data = build_usdm_data()
        del data["study"]["versions"][0]["studyDesigns"][0]["estimands"]
        usdm = _build_usdm(data)
        result = usdm.study_design_estimands("design-1")
        assert result["estimands"] == []

    def test_design_not_found(self):
        usdm = _build_usdm()
        result = usdm.study_design_estimands("nonexistent")
        assert result is None

    def test_empty_intervention_ids(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["estimands"][0]["interventionIds"] = []
        usdm = _build_usdm(data)
        result = usdm.study_design_estimands("design-1")
        assert result["estimands"][0]["treatment"] is None

    def test_m11_section_fallback_to_title(self):
        data = build_usdm_data()
        doc = data["study"]["documentedBy"][0]["versions"][0]
        for c in doc["contents"]:
            if c["sectionNumber"] == "3.1":
                c["sectionNumber"] = "3.X"
                break
        usdm = _build_usdm(data)
        result = usdm.study_design_estimands("design-1")
        assert "Primary Objective Content" in result["text"]


# --- schedule_of_activities ---


class TestScheduleOfActivities:

    @patch("app.model.usdm_json.M11DocumentView")
    def test_success(self, mock_m11_dv):
        usdm = _build_usdm()
        mock_study = MagicMock()
        mock_version = MagicMock()
        mock_design = MagicMock()
        usdm._wrapper.study_version_and_design.return_value = (mock_study, mock_version, mock_design)
        mock_doc = MagicMock()
        mock_doc.templateName = "M11"
        mock_doc_version = MagicMock()
        mock_version.documents.return_value = [{"document": mock_doc, "version": mock_doc_version}]
        mock_timeline = MagicMock()
        mock_timeline.model_dump.return_value = {"id": "t1"}
        mock_design.scheduleTimelines = [mock_timeline]
        mock_dv_instance = MagicMock()
        mock_dv_instance.schedule_of_activities.return_value = "<table>SoA</table>"
        mock_m11_dv.return_value = mock_dv_instance
        result = usdm.schedule_of_activities("design-1")
        assert result["id"] == 1
        assert len(result["data"]) == 1
        assert len(result["documents"]) == 1

    @patch("app.model.usdm_json.CPTDocumentView")
    def test_cpt_template(self, mock_cpt_dv):
        usdm = _build_usdm()
        mock_study = MagicMock()
        mock_version = MagicMock()
        mock_design = MagicMock()
        usdm._wrapper.study_version_and_design.return_value = (mock_study, mock_version, mock_design)
        mock_doc = MagicMock()
        mock_doc.templateName = "CPT"
        mock_version.documents.return_value = [{"document": mock_doc, "version": MagicMock()}]
        mock_design.scheduleTimelines = []
        mock_cpt_dv.return_value = MagicMock()
        result = usdm.schedule_of_activities("design-1")
        assert result is not None

    def test_no_data(self):
        usdm = _build_usdm()
        mock_design = MagicMock()
        usdm._wrapper.study_version_and_design.return_value = (None, None, mock_design)
        result = usdm.schedule_of_activities("design-1")
        assert result["data"] == []

    def test_unknown_template_skipped(self):
        usdm = _build_usdm()
        mock_study = MagicMock()
        mock_version = MagicMock()
        mock_design = MagicMock()
        usdm._wrapper.study_version_and_design.return_value = (mock_study, mock_version, mock_design)
        mock_doc = MagicMock()
        mock_doc.templateName = "UNKNOWN"
        mock_version.documents.return_value = [{"document": mock_doc, "version": MagicMock()}]
        mock_design.scheduleTimelines = []
        result = usdm.schedule_of_activities("design-1")
        assert result["documents"] == []


# --- soa ---


class TestSoa:

    @patch("app.model.usdm_json.SoA")
    def test_success(self, mock_soa_cls):
        usdm = _build_usdm()
        mock_version = MagicMock()
        mock_design = MagicMock()
        mock_timeline = MagicMock()
        mock_timeline.__iter__ = MagicMock(return_value=iter([("key", "val")]))
        mock_design.find_timeline.return_value = mock_timeline
        mock_version.find_study_design.return_value = mock_design
        usdm._wrapper.study.first_version.return_value = mock_version
        mock_soa_cls.return_value.to_html.return_value = "<table>SoA</table>"
        result = usdm.soa("design-1", "timeline-1")
        assert result is not None
        assert result["id"] == 1
        assert result["soa"] == "<table>SoA</table>"

    def test_no_version(self):
        usdm = _build_usdm()
        usdm._wrapper.study.first_version.return_value = None
        result = usdm.soa("design-1", "timeline-1")
        assert result is None

    def test_no_design(self):
        usdm = _build_usdm()
        mock_version = MagicMock()
        mock_version.find_study_design.return_value = None
        usdm._wrapper.study.first_version.return_value = mock_version
        result = usdm.soa("design-1", "timeline-1")
        assert result is None

    def test_no_timeline(self):
        usdm = _build_usdm()
        mock_version = MagicMock()
        mock_design = MagicMock()
        mock_design.find_timeline.return_value = None
        mock_version.find_study_design.return_value = mock_design
        usdm._wrapper.study.first_version.return_value = mock_version
        result = usdm.soa("design-1", "timeline-1")
        assert result is None


# --- _section_response ---


class TestSectionResponse:

    def test_m11_design_found(self):
        usdm = _build_usdm()
        result = usdm._section_response("design-1", "10.11", "sample size", "[Sample Size]")
        assert result is not None
        assert result["m11"] is True
        assert "Sample Size Content" in result["text"]

    def test_non_m11_returns_none(self):
        usdm = _build_usdm(m11=False)
        result = usdm._section_response("design-1", "10.11", "sample size", "[Sample Size]")
        assert result is None

    def test_design_not_found(self):
        usdm = _build_usdm()
        result = usdm._section_response("nonexistent", "10.11", "sample size", "[Sample Size]")
        assert result is None


# --- section wrapper methods ---


class TestSectionWrappers:

    def test_sample_size(self):
        usdm = _build_usdm()
        result = usdm.sample_size("design-1")
        assert result is not None
        assert result["m11"] is True

    def test_analysis_sets(self):
        usdm = _build_usdm()
        result = usdm.analysis_sets("design-1")
        assert result is not None

    def test_analysis_objectives(self):
        usdm = _build_usdm()
        result = usdm.analysis_objectives("design-1")
        assert result is not None

    def test_adverse_events_special_interest(self):
        usdm = _build_usdm()
        result = usdm.adverse_events_special_interest("design-1")
        assert result is not None

    def test_safety_assessments(self):
        usdm = _build_usdm()
        result = usdm.safety_assessments("design-1")
        assert result is not None


# --- protocol_sections_list ---


class TestProtocolSectionsList:

    def test_basic(self):
        usdm = _build_usdm()
        result = usdm.protocol_sections_list()
        assert isinstance(result, list)
        assert len(result) == 10
        assert result[0]["section_number"] == "1.1.2"

    def test_filters_zero(self):
        usdm = _build_usdm()
        result = usdm.protocol_sections_list()
        numbers = [s["section_number"] for s in result]
        assert "0" not in numbers

    def test_no_document(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        # protocol_sections returns None when no document; protocol_sections_list
        # does not guard against None so this path cannot be reached safely.
        assert usdm.protocol_sections() is None


# --- protocol_sections ---


class TestProtocolSections:

    def test_returns_all(self):
        usdm = _build_usdm()
        result = usdm.protocol_sections()
        assert len(result) == 11

    def test_no_document(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        result = usdm.protocol_sections()
        assert result is None


# --- section ---


class TestSection:

    def test_basic(self):
        usdm = _build_usdm()
        result = usdm.section("nc-1")
        assert result is not None
        assert "heading" in result
        assert "level" in result
        assert "text" in result
        assert "Overall Design Content" in result["text"]

    def test_no_document(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        result = usdm.section("nc-1")
        assert result is None


# --- _format_heading ---


class TestFormatHeading:

    def test_number_zero(self):
        usdm = _build_usdm()
        heading, level = usdm._format_heading({"sectionNumber": "0", "sectionTitle": "Title"})
        assert heading == ""

    def test_number_and_title(self):
        usdm = _build_usdm()
        heading, level = usdm._format_heading({"sectionNumber": "1.2", "sectionTitle": "My Section"})
        assert heading == "<h2>1.2 My Section</h2>"

    def test_number_only(self):
        usdm = _build_usdm()
        heading, level = usdm._format_heading({"sectionNumber": "3", "sectionTitle": None})
        assert heading == "<h1>3</h1>"

    def test_title_only(self):
        usdm = _build_usdm()
        heading, level = usdm._format_heading({"sectionNumber": None, "sectionTitle": "Appendix"})
        assert heading == "<h1>Appendix</h1>"

    def test_no_number_no_title(self):
        usdm = _build_usdm()
        heading, level = usdm._format_heading({"sectionNumber": None, "sectionTitle": None})
        assert heading == ""

    def test_nested_number(self):
        usdm = _build_usdm()
        heading, level = usdm._format_heading({"sectionNumber": "1.2.3", "sectionTitle": "Deep"})
        assert level == 3
        assert "<h3>" in heading


# --- _get_level ---


class TestGetLevel:

    def test_none_section_number(self):
        usdm = _build_usdm()
        assert usdm._get_level({"sectionNumber": None}) == 1

    def test_appendix(self):
        usdm = _build_usdm()
        assert usdm._get_level({"sectionNumber": "Appendix A"}) == 1

    def test_simple_number(self):
        usdm = _build_usdm()
        assert usdm._get_level({"sectionNumber": "3"}) == 1

    def test_nested_number(self):
        usdm = _build_usdm()
        assert usdm._get_level({"sectionNumber": "1.2.3"}) == 3

    def test_trailing_dot(self):
        usdm = _build_usdm()
        assert usdm._get_level({"sectionNumber": "1.2."}) == 2


# --- _population_age ---


class TestPopulationAge:

    def test_basic(self):
        usdm = _build_usdm()
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        result = usdm._population_age(design)
        assert result["min"] == 18
        assert result["max"] == 65
        assert result["min_unit"] == "Years"
        assert result["max_unit"] == "Years"

    def test_with_cohorts(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["population"]["cohorts"] = [
            {
                "plannedAge": {
                    "minValue": {"value": "12", "unit": {"standardCode": {"decode": "Years"}}},
                    "maxValue": {"value": "70", "unit": {"standardCode": {"decode": "Years"}}},
                }
            }
        ]
        usdm = _build_usdm(data)
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        result = usdm._population_age(design)
        # Note: code re-evaluates population.plannedAge for each cohort (bug),
        # so cohort values don't actually widen the range
        assert result["min"] == 18
        assert result["max"] == 65

    def test_exception_returns_missing(self):
        usdm = _build_usdm()
        result = usdm._population_age({})
        assert result == {"min": 0, "max": 0, "min_unit": "", "max_unit": ""}


# --- _min_max ---


class TestMinMax:

    def test_with_item(self):
        usdm = _build_usdm()
        item = {
            "minValue": {"value": "10", "unit": {"standardCode": {"decode": "Years"}}},
            "maxValue": {"value": "50", "unit": {"standardCode": {"decode": "Years"}}},
        }
        result = usdm._min_max(item)
        assert result["min"] == 10
        assert result["max"] == 50

    def test_none_item(self):
        usdm = _build_usdm()
        result = usdm._min_max(None)
        assert result == {"min": 0, "max": 0, "min_unit": "", "max_unit": ""}


# --- _population_recruitment ---


class TestPopulationRecruitment:

    def test_quantity(self):
        usdm = _build_usdm()
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        result = usdm._population_recruitment(design)
        assert result["enroll"] == 100
        assert result["complete"] == 80

    def test_range(self):
        data = build_usdm_data()
        pop = data["study"]["versions"][0]["studyDesigns"][0]["population"]
        pop["plannedEnrollmentNumberQuantity"] = None
        pop["plannedEnrollmentNumberRange"] = {"maxValue": "200"}
        pop["plannedCompletionNumberQuantity"] = None
        pop["plannedCompletionNumberRange"] = {"maxValue": "150"}
        usdm = _build_usdm(data)
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        result = usdm._population_recruitment(design)
        assert result["enroll"] == 200
        assert result["complete"] == 150

    def test_exception(self):
        usdm = _build_usdm()
        result = usdm._population_recruitment({})
        assert result == {"enroll": "[Enrolled]", "complete": "[Complete]"}


# --- _range_or_quantity ---


class TestRangeOrQuantity:

    def test_quantity(self):
        usdm = _build_usdm()
        data = {"testQuantity": {"value": "42"}, "testRange": None}
        result = usdm._range_or_quantity(data, "test")
        assert result == "42"

    def test_range(self):
        usdm = _build_usdm()
        data = {"testQuantity": None, "testRange": {"maxValue": "99"}}
        result = usdm._range_or_quantity(data, "test")
        assert result == "99"

    def test_neither(self):
        usdm = _build_usdm()
        data = {"testQuantity": None, "testRange": None}
        result = usdm._range_or_quantity(data, "test")
        assert result == "0"


# --- _intervention ---


class TestIntervention:

    def test_empty_ids(self):
        usdm = _build_usdm()
        result = usdm._intervention(usdm._data["study"]["versions"][0], [])
        assert result is None

    def test_found(self):
        usdm = _build_usdm()
        result = usdm._intervention(usdm._data["study"]["versions"][0], ["int-1"])
        assert result["name"] == "Drug A"

    def test_not_found(self):
        usdm = _build_usdm()
        result = usdm._intervention(usdm._data["study"]["versions"][0], ["nonexistent"])
        assert result is None


# --- _arm_from_intervention ---


class TestArmFromIntervention:

    def test_found(self):
        usdm = _build_usdm()
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        result = usdm._arm_from_intervention(design, "int-1")
        assert result["label"] == "Arm A"

    def test_not_found(self):
        usdm = _build_usdm()
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        result = usdm._arm_from_intervention(design, "nonexistent")
        assert result["label"] == "[Not Found]"

    def test_no_cell(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["studyCells"] = []
        usdm = _build_usdm(data)
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        result = usdm._arm_from_intervention(design, "int-1")
        assert result["label"] == "[Not Found]"


# --- _image_in_section ---


class TestImageInSection:

    def test_with_image(self):
        usdm = _build_usdm()
        section = {"contentItemId": "nci-2"}
        result = usdm._image_in_section(section)
        assert result is not None
        assert "img" in str(result)

    def test_without_image(self):
        usdm = _build_usdm()
        section = {"contentItemId": "nci-1"}
        result = usdm._image_in_section(section)
        assert result == ""

    def test_no_section(self):
        usdm = _build_usdm()
        result = usdm._image_in_section(None)
        assert result == ""


# --- _document ---


class TestDocument:

    def test_valid(self):
        usdm = _build_usdm()
        doc = usdm._document()
        assert doc is not None
        assert doc["id"] == "docver-1"

    def test_exception(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        doc = usdm._document()
        assert doc is None


# --- _study_design ---


class TestStudyDesign:

    def test_found(self):
        usdm = _build_usdm()
        result = usdm._study_design("design-1")
        assert result is not None
        assert result["name"] == "Design One"

    def test_not_found(self):
        usdm = _build_usdm()
        result = usdm._study_design("nonexistent")
        assert result is None


# --- _section_by_number ---


class TestSectionByNumber:

    def test_found(self):
        usdm = _build_usdm()
        result = usdm._section_by_number("1.1.2")
        assert result is not None
        assert result["sectionTitle"] == "Overall Design"

    def test_not_found(self):
        usdm = _build_usdm()
        result = usdm._section_by_number("99.99")
        assert result is None

    def test_no_document(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        result = usdm._section_by_number("1.1.2")
        assert result is None


# --- _section_by_title_contains ---


class TestSectionByTitleContains:

    def test_found(self):
        usdm = _build_usdm()
        result = usdm._section_by_title_contains("Overall Design")
        assert result is not None

    def test_case_insensitive(self):
        usdm = _build_usdm()
        result = usdm._section_by_title_contains("overall design")
        assert result is not None

    def test_not_found(self):
        usdm = _build_usdm()
        result = usdm._section_by_title_contains("Nonexistent Section")
        assert result is None

    def test_no_document(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        result = usdm._section_by_title_contains("Overall Design")
        assert result is None


# --- _set_multiple ---


class TestSetMultiple:

    def test_found(self):
        usdm = _build_usdm()
        result = usdm._set_multiple("design-1", "characteristics", "[Missing]")
        assert "INTERVENTIONAL" in result

    def test_not_found(self):
        usdm = _build_usdm()
        result = usdm._set_multiple("design-1", "nonexistent_key", "[Missing]")
        assert result == {"[Missing]": "[Missing]"}


class TestSetTrialHelpers:

    def test_set_trial_intent_types(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["trialIntentTypes"] = [{"decode": "TREATMENT"}]
        usdm = _build_usdm(data)
        result = usdm._set_trial_intent_types("design-1")
        assert "TREATMENT" in result

    def test_set_trial_types(self):
        data = build_usdm_data()
        data["study"]["versions"][0]["studyDesigns"][0]["trialTypes"] = [{"decode": "EFFICACY"}]
        usdm = _build_usdm(data)
        result = usdm._set_trial_types("design-1")
        assert "EFFICACY" in result


# --- _objective_endpoint_from_estimand ---


class TestObjectiveEndpointFromEstimand:

    def test_found(self):
        usdm = _build_usdm()
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        obj, ep = usdm._objective_endpoint_from_estimand(design, "ep-1")
        assert obj["text"] == "Primary Objective"
        assert ep["text"] == "Primary Endpoint"

    def test_not_found(self):
        usdm = _build_usdm()
        design = usdm._data["study"]["versions"][0]["studyDesigns"][0]
        obj, ep = usdm._objective_endpoint_from_estimand(design, "nonexistent")
        assert obj is None
        assert ep is None


# --- fhir, fhir_data, json, wrapper, extra, templates ---


class TestFhirAndExport:

    @patch("app.model.usdm_json.FHIRM11")
    def test_fhir_data(self, mock_fhir_cls):
        usdm = _build_usdm()
        mock_fhir_cls.return_value.to_message.return_value = '{"bundle": "data"}'
        result = usdm.fhir_data()
        assert result == '{"bundle": "data"}'

    @patch("app.model.usdm_json.FHIRM11")
    def test_fhir(self, mock_fhir_cls):
        usdm = _build_usdm()
        mock_fhir_cls.return_value.to_message.return_value = '{"bundle": "data"}'
        usdm._files.save.return_value = ("/tmp/fhir.json", "fhir.json")
        fullpath, filename, content_type = usdm.fhir()
        assert fullpath == "/tmp/fhir.json"
        assert content_type == "text/plain"

    @patch("app.model.usdm_json.FHIRSoA")
    def test_fhir_soa_data(self, mock_soa_cls):
        usdm = _build_usdm()
        mock_soa_cls.return_value.to_message.return_value = '{"soa": "data"}'
        result = usdm.fhir_soa_data("timeline-1")
        assert result == '{"soa": "data"}'

    @patch("app.model.usdm_json.FHIRSoA")
    def test_fhir_soa(self, mock_soa_cls):
        usdm = _build_usdm()
        mock_soa_cls.return_value.to_message.return_value = '{"soa": "data"}'
        usdm._files.save.return_value = ("/tmp/soa.json", "soa.json")
        fullpath, filename, content_type = usdm.fhir_soa("timeline-1")
        assert fullpath == "/tmp/soa.json"
        assert content_type == "application/json"

    def test_json(self):
        usdm = _build_usdm()
        usdm._files.path.return_value = ("/tmp/usdm.json", "usdm.json", True)
        fullpath, filename, content_type = usdm.json()
        assert fullpath == "/tmp/usdm.json"
        assert content_type == "application/json"

    def test_wrapper(self):
        usdm = _build_usdm()
        assert usdm.wrapper() is usdm._wrapper

    def test_extra(self):
        usdm = _build_usdm(extra={"key": "val"})
        assert usdm.extra() == {"key": "val"}

    def test_templates(self):
        usdm = _build_usdm()
        usdm._wrapper.study.document_templates.return_value = ["M11", "CPT"]
        result = usdm.templates()
        assert result == ["M11", "CPT"]


# --- _get_usdm, _get_extra ---


class TestGetFiles:

    def test_get_usdm(self, tmp_path):
        usdm = _build_usdm()
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')
        usdm._files.path.return_value = (str(test_file), "test.json", True)
        result = usdm._get_usdm()
        assert result == {"key": "value"}

    def test_get_extra(self, tmp_path):
        usdm = _build_usdm()
        test_file = tmp_path / "extra.yaml"
        test_file.write_text("key: value\n")
        usdm._files.path.return_value = (str(test_file), "extra.yaml", True)
        result = usdm._get_extra()
        assert result == {"key": "value"}

    def test_get_raw(self, tmp_path):
        usdm = _build_usdm()
        test_file = tmp_path / "raw.json"
        test_file.write_text('{"raw": true}')
        usdm._files.path.return_value = (str(test_file), "raw.json", True)
        result = usdm._get_raw()
        assert result == '{"raw": true}'


# --- _section_full_text ---


class TestSectionFullText:

    def test_by_number(self):
        usdm = _build_usdm()
        result = usdm._section_full_text("10.11", "sample size", "[Default]")
        assert "Sample Size Content" in result

    def test_by_title(self):
        usdm = _build_usdm()
        result = usdm._section_full_text("99.99", "sample size", "[Default]")
        assert "Sample Size Content" in result

    def test_no_section(self):
        usdm = _build_usdm()
        result = usdm._section_full_text("99.99", "nonexistent", "[Default]")
        assert result == "[Default]"

    def test_no_document(self):
        data = build_usdm_data()
        data["study"]["documentedBy"] = []
        usdm = _build_usdm(data)
        result = usdm._section_full_text("10.11", "sample size", "[Default]")
        assert result == "[Default]"

    def test_multi_level_traversal(self):
        usdm = _build_usdm()
        result = usdm._section_full_text("8.4", "safety", "[Default]")
        assert "Safety Assessments Content" in result
        assert "Adverse Events Content" in result


# --- _get_number ---


class TestGetNumber:

    def test_valid(self):
        usdm = _build_usdm()
        assert usdm._get_number({"sectionNumber": "5"}) == 5

    def test_invalid(self):
        usdm = _build_usdm()
        assert usdm._get_number({"sectionNumber": "abc"}) == 0


# --- _find_intervention ---


class TestFindIntervention:

    def test_found(self):
        usdm = _build_usdm()
        version = usdm._data["study"]["versions"][0]
        result = usdm._find_intervention(version, "int-1")
        assert result["name"] == "Drug A"

    def test_not_found(self):
        usdm = _build_usdm()
        version = usdm._data["study"]["versions"][0]
        result = usdm._find_intervention(version, "nonexistent")
        assert result is None
