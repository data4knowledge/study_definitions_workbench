from app.model.fhir.to_fhir import ToFHIR
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.researchstudy import ResearchStudy
from usdm_model.study_version import StudyVersion
from uuid import uuid4

import datetime

class ToFHIRV2(ToFHIR):

  class LogicError(Exception):
    pass

  def to_fhir(self, uuid: uuid4):
    try:
      research_study = self._research_study()
      sections = []
      root = self.protocol_document_version.contents[0]
      for id in root.childIds:
        content = next((x for x in self.protocol_document_version.contents if x.id == id), None)
        sections.append(self._content_to_section(content))
      type_code = CodeableConcept(text=f"EvidenceReport")
      date = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
      author = Reference(display="USDM")
      composition = Composition(title=self.doc_title, type=type_code, section=sections, date=date, status="preliminary", author=[author])
      identifier = Identifier(system='urn:ietf:rfc:3986', value=f'urn:uuid:{uuid}')
      bundle_entry_1 = BundleEntry(resource=composition, fullUrl="https://www.example.com/Composition/1234")
      bundle_entry_2 = BundleEntry(resource=research_study, fullUrl="https://www.example.com/Composition/1234")
      bundle = Bundle(id=None, entry=[bundle_entry_1, bundle_entry_2], type="document", identifier=identifier, timestamp=date)
      return bundle.json()
    except Exception as e:
      self._errors_and_logging.exception(f"Exception raised generating FHIR content. See logs for more details", e)
      return None

  def _research_study(self) -> ResearchStudy:
    version = self.study_version
    result = ResearchStudy(status='draft', identifier=[])
    result.title = self.get_title('Official Study Title').text
    phase = self.phase()
    phase_code = Coding(system=phase.codeSystem, version=phase.codeSystemVersion, code=phase.code, display=phase.decode)
    result.phase = CodeableConcept(coding=[phase_code], text=phase.decode)
    result.version = version.versionIdentifier
    for identifier in version.studyIdentifiers:
      identifier_code = CodeableConcept(text=f"{identifier.studyIdentifierScope.organizationType.decode}")
      result.identifier.append({'type': identifier_code, 'value': identifier.studyIdentifier})
    print(f"RESEARCH STUDY: {result}")
    return result
  
  def get_title(self, title_type):
    for title in self.study_version.titles:
      if title.type.decode == title_type:
        return title
    return None

  def sponsor_identifier(self):
    for identifier in self.study_version.studyIdentifiers:
      if identifier.scope.organizationType.code == 'C70793':
        return identifier
    return None

  def phase(self):
    return self.study_version.studyPhase.standardCode