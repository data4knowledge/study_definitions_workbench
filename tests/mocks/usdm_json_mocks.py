def mock_usdm_json_init(mocker, path="app.main"):
    mock = mocker.patch(f"{path}.USDMJson.__init__")
    mock.side_effect = [None]
    return mock


def mock_usdm_json_timelines(mocker, path="app.main"):
    mock = mocker.patch(f"{path}.USDMJson.timelines")
    data = {
        "id": "1",
        "study_id": "2",
        "m11": False,
        "timelines": [
            {
                "id": "3",
                "name": "Special Timeline",
            }
        ],
    }
    mock.side_effect = [data]
    return mock


def mock_usdm_json_soa(mocker, path="app.main"):
    mock = mocker.patch(f"{path}.USDMJson.soa")
    data = {
        "timeline": {
            "label": "SOA LABEL",
            "description": "SOA Description",
            "mainTimeline": False,
            "name": "SoA Name",
        },
        "soa": "<table>SOA Table</table>",
    }
    mock.side_effect = [data]
    return mock


def mock_usdm_study_version(mocker, path="app.main"):
    mock = mocker.patch(f"{path}.USDMJson.study_version")
    mock.side_effect = [
        {
            "id": "1",
            "version_identifier": "1",
            "identifiers": {"Clinical Study Sponsor": "Identifier For Test"},
            "titles": {"Official Study Title": "The Offical Study Title For Test"},
            "study_designs": {
                "xxx": {
                    "id": "2", 
                    "name": "design name", 
                    "label": "design label", 
                }
            },
            "phase": "Phase For Test"
        }
    ]
    return mock


def mock_usdm_json_fhir_soa(mocker, path="app.main"):
    mock = mocker.patch(f"{path}.USDMJson.fhir_soa")
    mock.side_effect = [
        ("tests/test_files/main/simple.txt", "simple.txt", "text/plain")
    ]
    return mock


def mock_usdm_json_fhir_soa_error(mocker, path="app.main"):
    mock = mocker.patch(f"{path}.USDMJson.fhir_soa")
    data = ("", "", "")
    mock.side_effect = [data]
    return mock
