from app.model.fhir.to_fhir import ToFHIR
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from fhir.resources.researchstudy import ResearchStudy
from uuid import uuid4

import datetime

class ToFHIRV2(ToFHIR):

  class LogicError(Exception):
    pass

  def to_fhir(self, uuid: uuid4):
    try:
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
      bundle_entry = BundleEntry(resource=composition, fullUrl="https://www.example.com/Composition/1234")
      bundle = Bundle(id=None, entry=[bundle_entry], type="document", identifier=identifier, timestamp=date)
      return bundle.json()
    except Exception as e:
      self._errors_and_logging.exception(f"Exception raised generating FHIR content. See logs for more details", e)
      return None

  def _research_study(self) -> ResearchStudy:
    version = self.study_version
    result = ResearchStudy()
    # result = {
    #   'id': self.id,
    #   'version_identifier': version['versionIdentifier'],
    #   'identifiers': {},
    #   'titles': {},
    #   'study_designs': {},
    #   'phase': ''
    # }
    # for identifier in version['studyIdentifiers']:
    #   result['identifiers'][identifier['studyIdentifierScope']['organizationType']['decode']] = identifier
    # for title in version['titles']:
    #   result['titles'][title['type']['decode']] = title['text']
    # for design in version['studyDesigns']:
    #   result['study_designs'][design['id']] = {'id': design['id'], 'name': design['name'], 'label': design['label']}
    # result['phase'] = version['studyPhase']
    return result