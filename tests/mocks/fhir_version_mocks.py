TEST_FHIR_VERSIONS = {
    "1": "Mock Connectathon 1",
    "2": "Mock Connectathon 2",
    "3": "Mock Connectathon 3",
    "4": "Mock Connectathon 4",
}


def mock_fhir_versions(mocker, path="app.routers.transmissions"):
    mock = mocker.patch(f"{path}.fhir_versions")
    mock.side_effect = [TEST_FHIR_VERSIONS]
    return mock


def mock_check_fhir_version(mocker, path="app.routers.transmissions"):
    mock = mocker.patch(f"{path}.checK_fhir_version")
    mock.side_effect = [
        ("Mock V1", "Mock Connectathon 1"),
        ("Mock V2", "Mock Connectathon 2"),
        ("Mock V3", "Mock Connectathon 3"),
    ]
    return mock


# def mock_fhir_version_description(mocker, path="app.routers.transmissions"):
#     mock = mocker.patch(f"{path}.fhir_version_description")
#     mock.side_effect = [
#         "Mock Connectathon 1",
#         "Mock Connectathon 2",
#         "Mock Connectathon 3",
#     ]
#     return mock
