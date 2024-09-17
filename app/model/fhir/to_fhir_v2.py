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
from fhir.resources.researchstudy import ResearchStudyAssociatedParty
from fhir.resources.researchstudy import ResearchStudyProgressStatus
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
    result = ResearchStudy(status='draft', identifier=[], extension=[], label=[], associatedParty=[], progressStatus=[])

    # Sponsor Confidentiality Statememt
    ext = self._extension("research-study-sponsor-confidentiality-statement", self._extensions['sponsor_confidentiality'])
    if ext:
      result.extension.append(ext)
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
    x = self._extensions['original_protocol']
    # Version Number
    result.version = version.versionIdentifier
    # Version Date
    approval_date = self._document_approval_date()
    if approval_date:
      result.date = approval_date.dateValue
    # Amendment Identifier
    result.identifier.append({'type': 'Amendment Identifier', 'value': self._extensions['amendment_identifier']})    
    # Amendment Scope
    x = self._extensions['amendment_scope']
    # Compound Codes
    x = self._extensions['compound_codes']
    # Compund Names
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
    x = self._extensions['sponsor_name_and_address']
    # result.associatedParty.append()
    # Manufacturer Name and Address
    x = self._extensions['manufacturer_name_and_address']
    # Regulatory Agency Identifiers
    x = self._extensions['regulatory_agency_identifiers']
    # Sponsor Approval
    result.progressStatus.append(self._progress_status(self._extensions['sponsor_approval_date'], 'sponsor-approved', 'sponsor apporval date'))
    # Sponsor Signatory
    result.associatedParty.append(self._associated_party(self._extensions['sponsor_signatory'], 'sponsor-signatory', 'sponsor signatory'))
    # Medical Expert Contact
    result.associatedParty.append(self._associated_party(self._extensions['medical_expert_contact'], 'medical-expert', 'medical expert'))
    # SAE Reporting Method
    ext = self._extension("research-study-sae-reporting-method", self._extensions['sae_reporting_method'])
    if ext:
      result.extension.append(ext)
    print(f"RESEARCH STUDY: {result.to_json()}")
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
    
  def _coding_from_code(self, code: USDMCode):
    return Coding(system=code.codeSystem, version=code.codeSystemVersion, code=code.code, display=code.decode)
  
  def _associated_party(self, value: str, role_code: str, role_display: str):
    code = Coding(system='http://hl7.org/fhir/research-study-party-role', code=role_code, display=role_display)
    role = CodeableConcept(coding=[code])
    return ResearchStudyAssociatedParty(role=role, party={'display': value})

  def _progress_status(self, value: str, state_code: str, state_display: str):
    code = Coding(system='http://hl7.org/fhir/research-study-party-role', code=state_code, display=state_display)
    state = CodeableConcept(coding=[code])
    return ResearchStudyProgressStatus(state=state, period={'start': value})
  
  def _extension(self, key: str, value: str):
    return Extension(url=f"http://hl7.org/fhir/uv/ebm/StructureDefinition/{key}", valueString=value) if value else None
