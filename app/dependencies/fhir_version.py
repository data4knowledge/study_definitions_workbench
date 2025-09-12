FHIR_VERSIONS = {
    "prism2": {"description": "Dallas (PRISM 2)", "import": True, "export": True, "transmit": False},
    "madrid": {"description": "Madrid", "import": False, "export": True, "transmit": False},
    "prism3": {"description": "Pittsburgh (PRISM 3)", "import": False, "export": True, "transmit": True},
}


def fhir_versions() -> list:
    return list(FHIR_VERSIONS.keys())


def check_fhir_version(version: str) -> tuple[bool, str]:
    return version in FHIR_VERSIONS, fhir_version_description(version)


def fhir_version_description(version: str) -> str:
    return FHIR_VERSIONS[version]["description"] if version in FHIR_VERSIONS else "FHIR Version not supported"

def fhir_version_import(version: str) -> bool:
    return FHIR_VERSIONS[version]["import"] if version in FHIR_VERSIONS else False

def fhir_version_export(version: str) -> bool:
    return FHIR_VERSIONS[version]["export"] if version in FHIR_VERSIONS else False

def fhir_version_transmit(version: str) -> bool:
    return FHIR_VERSIONS[version]["transmit"] if version in FHIR_VERSIONS else False
