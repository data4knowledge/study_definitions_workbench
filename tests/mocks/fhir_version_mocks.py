TEST_FHIR_VERSIONS = {
    "prism2": {"description": "Dallas (PRISM 2)", "import": True, "export": True, "transmit": False},
    "madrid": {"description": "Madrid", "import": False, "export": True, "transmit": False},
    "prism3": {"description": "Pittsburgh (PRISM 3)", "import": True, "export": True, "transmit": True},
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
