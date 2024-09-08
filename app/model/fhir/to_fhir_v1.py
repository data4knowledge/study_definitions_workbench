from app.model.fhir.to_fhir import ToFHIR
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from uuid import uuid4
import datetime

class ToFHIRV1(ToFHIR):

  class LogicError(Exception):
    pass

  def to_fhir(self):
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
      identifier = Identifier(system='urn:ietf:rfc:3986', value=f'urn:uuid:{self._uuid}')
      bundle_entry = BundleEntry(resource=composition, fullUrl="https://www.example.com/Composition/1234")
      bundle = Bundle(id=None, entry=[bundle_entry], type="document", identifier=identifier, timestamp=date)
      return bundle.json()
    except Exception as e:
      self._errors_and_logging.exception(f"Exception raised generating FHIR content. See logs for more details", e)
      return None

