
FHIR_VERSIONS = {'1': "Dallas connectathon"}

def check_fhir_version(version: str) -> tuple[bool, str]:
  if version in FHIR_VERSIONS:
    return True, FHIR_VERSIONS[version]  
  else:
    return False, ''
  