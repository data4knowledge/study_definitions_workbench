def build_usdm_data():
    """Build a minimal but realistic USDM study dict for testing all data-extraction methods."""
    return {
        "study": {
            "versions": [_build_version()],
            "documentedBy": [{"versions": [_build_document()]}],
        },
    }


def _build_version():
    return {
        "versionIdentifier": "v1.0",
        "organizations": [
            {
                "id": "org-1",
                "name": "Pharma Corp",
                "label": "Pharma Label",
                "type": {"code": "C54149", "decode": "Pharmaceutical Company"},
            },
            {
                "id": "org-2",
                "name": "Regulatory",
                "type": {"code": "C188863", "decode": "Regulatory Agency"},
            },
        ],
        "studyIdentifiers": [
            {"scopeId": "org-1", "text": "STUDY-001"},
            {"scopeId": "org-2", "text": "REG-002"},
        ],
        "titles": [
            {"type": {"code": "C207616", "decode": "Official Study Title"}, "text": "Test Study"},
            {"type": {"code": "C207615", "decode": "Brief Study Title"}, "text": "Brief Test"},
        ],
        "studyDesigns": [_build_design()],
        "studyInterventions": [
            {"id": "int-1", "name": "Drug A"},
        ],
        "narrativeContentItems": [
            {"id": "nci-0", "text": ""},
            {"id": "nci-1", "text": "<p>Overall Design Content</p>"},
            {"id": "nci-2", "text": "<p>Trial Schema</p><img src='schema.png'/>"},
            {"id": "nci-3", "text": "<p>Primary Objective Content</p>"},
            {"id": "nci-4", "text": "<p>Trial Intervention Content</p>"},
            {"id": "nci-5", "text": "<p>Safety Assessments Content</p>"},
            {"id": "nci-6", "text": "<p>Adverse Events Content</p>"},
            {"id": "nci-7", "text": "<p>Analysis Sets Content</p>"},
            {"id": "nci-8", "text": "<p>Analysis Objectives Content</p>"},
            {"id": "nci-9", "text": "<p>Sample Size Content</p>"},
            {"id": "nci-10", "text": "<p>References</p>"},
        ],
        "documentVersionIds": ["docver-1"],
    }


def _build_design():
    return {
        "id": "design-1",
        "name": "Design One",
        "label": "Design Label",
        "studyPhase": {"standardCode": {"decode": "Phase III"}},
        "model": {"decode": "PARALLEL"},
        "arms": [
            {"id": "arm-1", "label": "Arm A", "type": {"decode": "Active"}},
        ],
        "blindingSchema": {"standardCode": {"decode": "DOUBLE_BLIND"}},
        "population": {
            "plannedAge": {
                "minValue": {
                    "value": "18",
                    "unit": {"standardCode": {"decode": "Years"}},
                },
                "maxValue": {
                    "value": "65",
                    "unit": {"standardCode": {"decode": "Years"}},
                },
            },
            "cohorts": [],
            "plannedEnrollmentNumberQuantity": {"value": "100"},
            "plannedEnrollmentNumberRange": None,
            "plannedCompletionNumberQuantity": {"value": "80"},
            "plannedCompletionNumberRange": None,
        },
        "characteristics": [{"decode": "INTERVENTIONAL"}],
        "studyInterventionIds": ["int-1"],
        "studyCells": [{"id": "arm-1", "elementIds": ["int-1"]}],
        "estimands": [
            {
                "interventionIds": ["int-1"],
                "populationSummary": "Mean difference",
                "analysisPopulationId": "pop-1",
                "intercurrentEvents": [],
                "variableOfInterestId": "ep-1",
            },
        ],
        "objectives": [
            {
                "id": "obj-1",
                "text": "Primary Objective",
                "endpoints": [
                    {"id": "ep-1", "text": "Primary Endpoint"},
                ],
            },
        ],
    }


def _build_document():
    return {
        "id": "docver-1",
        "contents": [
            {"id": "nc-0", "sectionNumber": "0", "sectionTitle": "Title Page", "contentItemId": "nci-0", "previousId": None, "nextId": "nc-1"},
            {"id": "nc-1", "sectionNumber": "1.1.2", "sectionTitle": "Overall Design", "contentItemId": "nci-1", "previousId": "nc-0", "nextId": "nc-2"},
            {"id": "nc-2", "sectionNumber": "1.2", "sectionTitle": "Trial Schema", "contentItemId": "nci-2", "previousId": "nc-1", "nextId": "nc-3"},
            {"id": "nc-3", "sectionNumber": "3.1", "sectionTitle": "Primary Objective", "contentItemId": "nci-3", "previousId": "nc-2", "nextId": "nc-4"},
            {"id": "nc-4", "sectionNumber": "6.1", "sectionTitle": "Trial Intervention", "contentItemId": "nci-4", "previousId": "nc-3", "nextId": "nc-5"},
            {"id": "nc-5", "sectionNumber": "8.4", "sectionTitle": "Safety Assessments and Procedures", "contentItemId": "nci-5", "previousId": "nc-4", "nextId": "nc-6"},
            {"id": "nc-6", "sectionNumber": "9.3.2", "sectionTitle": "Adverse Events of Special Interest", "contentItemId": "nci-6", "previousId": "nc-5", "nextId": "nc-7"},
            {"id": "nc-7", "sectionNumber": "10.2", "sectionTitle": "Analysis Sets", "contentItemId": "nci-7", "previousId": "nc-6", "nextId": "nc-8"},
            {"id": "nc-8", "sectionNumber": "10.4", "sectionTitle": "Analysis Associated with Primary", "contentItemId": "nci-8", "previousId": "nc-7", "nextId": "nc-9"},
            {"id": "nc-9", "sectionNumber": "10.11", "sectionTitle": "Sample Size", "contentItemId": "nci-9", "previousId": "nc-8", "nextId": "nc-10"},
            {"id": "nc-10", "sectionNumber": "11", "sectionTitle": "References", "contentItemId": "nci-10", "previousId": "nc-9", "nextId": None},
        ],
    }
