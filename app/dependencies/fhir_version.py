FHIR_VERSIONS = {
    "p2": "Dallas (PRISM 2)",
    "p3": "Pittsburgh (PRISM 3)",
}


def fhir_versions() -> list:
    return list(FHIR_VERSIONS.keys())


def check_fhir_version(version: str) -> tuple[bool, str]:
    return version in FHIR_VERSIONS, fhir_version_description(version)


def fhir_version_description(version: str) -> str:
    if version in FHIR_VERSIONS:
        return FHIR_VERSIONS[version]
    else:
        return "FHIR Version not supported"
