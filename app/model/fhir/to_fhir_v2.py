from app.model.fhir.to_fhir import ToFHIR
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.extension import Extension
from fhir.resources.fhirtypes import ResearchStudyLabelType
from usdm_model.code import Code as USDMCode
from usdm_model.study_title import StudyTitle as USDMStudyTitle
from usdm_model.governance_date import GovernanceDate as USDMGovernanceDate
from uuid import uuid4

import datetime

class ToFHIRV2(ToFHIR):

  class LogicError(Exception):
    pass

  def to_fhir(self) -> None:
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
      identifier = Identifier(system='urn:ietf:rfc:3986', value=f'urn:uuid:{self._uuid}')
      bundle_entry_1 = BundleEntry(resource=composition, fullUrl="https://www.example.com/Composition/1234")
      bundle_entry_2 = BundleEntry(resource=research_study, fullUrl="https://www.example.com/Composition/1234")
      bundle = Bundle(id=None, entry=[bundle_entry_1, bundle_entry_2], type="document", identifier=identifier, timestamp=date)
      return bundle.json()
    except Exception as e:
      self._errors_and_logging.exception(f"Exception raised generating FHIR content. See logs for more details", e)
      return None

  def _research_study(self) -> ResearchStudy:
    version = self.study_version
    result = ResearchStudy(status='draft', identifier=[], extension=[], label=[], associatedParty=[])

    # Sponsor Confidentiality Statememt
    cs = Extension(url="http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement", valueString=self._extensions['sponsor_confidentiality'])
    result.extension.append(cs)
    # Full Title
    result.title = self._get_title('Official Study Title').text
    # Trial Acronym
    acronym = self._get_title('Study Acronym')
    if acronym:
      type = CodeableConcept(coding=[self._coding_from_code(acronym.type)]) 
      result.label.append(ResearchStudyLabelType(type=type, value=acronym.text))
    # Sponsor Protocol Identifier
    for identifier in version.studyIdentifiers:
      identifier_code = CodeableConcept(text=f"{identifier.studyIdentifierScope.organizationType.decode}")
      result.identifier.append({'type': identifier_code, 'value': identifier.studyIdentifier})
    # Original Protocol
    # TBD
    # Version Number
    result.version = version.versionIdentifier
    # Version Date
    approval_date = self._document_approval_date()
    if approval_date:
      result.date = approval_date.dateValue
    # Amendment Identifier
    result.identifier.append({'type': 'Amendment Identifier', 'value': self._extensions['amendment_identifier']})    
    # Amendment Scope
    # TBD
    x = self._extensions['amendment_scope']
    # Compound Codes
    # TBD
    x = self._extensions['compound_codes']
    # Compund Names
    # TBD
    x = self._extensions['compound_names']
    # Trial Phase
    phase = self._phase()
    phase_code = Coding(system=phase.codeSystem, version=phase.codeSystemVersion, code=phase.code, display=phase.decode)
    result.phase = CodeableConcept(coding=[phase_code], text=phase.decode)
    # Short Title
    title = self._get_title('Brief Study Title')
    if title:
      type = CodeableConcept(coding=[self._coding_from_code(title.type)]) 
      result.label.append(ResearchStudyLabelType(type=type, value=title.text))    
    # Sponsor Name and Address
    # result.associatedParty.append()
    # Manufacturer Name and Address
    # Regulatory Agency Identifiers
    #  See above in identifiers
    # Sponsor Approval
    # Sponsor Signatory
    # Medical Expert Contact
    # SAE Reporting Method
    print(f"RESEARCH STUDY: {result}")
    return result
  
  def _sponsor_identifier(self):
    for identifier in self.study_version.studyIdentifiers:
      if identifier.scope.organizationType.code == 'C70793':
        return identifier
    return None

  def _phase(self):
    return self.study_version.studyPhase.standardCode

  def _document_approval_date(self) -> USDMGovernanceDate:
    dates = self.study_version.dateValues
    for date in dates:
      if date.type.code == 'C99903x1':
        return date
    return None
    
  def _coding_from_code(code: USDMCode):
    return Coding(system=code.codeSystem, version=code.codeSystemVersion, code=code.code, display=code.decode)