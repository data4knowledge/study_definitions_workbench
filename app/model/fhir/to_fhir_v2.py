from app.model.fhir.to_fhir import ToFHIR
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.identifier import Identifier
from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.reference import Reference
from fhir.resources.researchstudy import ResearchStudy
from fhir.resources.extension import Extension
from fhir.resources.researchstudy import ResearchStudyAssociatedParty
from fhir.resources.researchstudy import ResearchStudyProgressStatus
from fhir.resources.organization import Organization
from fhir.resources.extendedcontactdetail import ExtendedContactDetail
from fhir.resources.fhirtypes import ResearchStudyLabelType, AddressType
from usdm_model.code import Code as USDMCode
from usdm_model.study_title import StudyTitle as USDMStudyTitle
from usdm_model.governance_date import GovernanceDate as USDMGovernanceDate
from usdm_model.organization import Organization as USDMOrganization
from usdm_model.address import Address as USDMAddress
from usdm_model.study_version import StudyVersion as USDMStudyVersion
from uuid import uuid4

import datetime

class ToFHIRV2(ToFHIR):

  class LogicError(Exception):
    pass

  def to_fhir(self) -> None:
    try:
      self._entries = []
      self._entries.append({'item': self._research_study(), 'url': 'https://www.example.com/Composition/1234'})
      sections = []
      root = self.protocol_document_version.contents[0]
      for id in root.childIds:
        content = next((x for x in self.protocol_document_version.contents if x.id == id), None)
        sections.append(self._content_to_section(content))
      type_code = CodeableConcept(text=f"EvidenceReport")
      date = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
      author = Reference(display="USDM")
      self._entries.append({'item': Composition(title=self.doc_title, type=type_code, section=sections, date=date, status="preliminary", author=[author]), 'url': 'https://www.example.com/Composition/1234'})
      identifier = Identifier(system='urn:ietf:rfc:3986', value=f'urn:uuid:{self._uuid}')
      entries = []
      for entry in self._entries:
        entries.append(BundleEntry(resource=entry['item'], fullUrl=entry['url']))
      bundle = Bundle(id=None, entry=entries, type="document", identifier=identifier, timestamp=date)
      return bundle.json()
    except Exception as e:
      self._errors_and_logging.exception(f"Exception raised generating FHIR content. See logs for more details", e)
      return None

  def _research_study(self) -> ResearchStudy:
    version = self.study_version
    result = ResearchStudy(status='draft', identifier=[], extension=[], label=[], associatedParty=[], progressStatus=[])

    # Sponsor Confidentiality Statememt
    ext = self._extension("research-study-sponsor-confidentiality-statement", self._title_page['sponsor_confidentiality'])
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
    
    # Original Protocol - No implementation details currently
    x = self._title_page['original_protocol']
    
    # Version Number
    result.version = version.versionIdentifier
    
    # Version Date
    approval_date = self._document_approval_date()
    if approval_date:
      result.date = approval_date.dateValue
    
    # Amendment Identifier
    result.identifier.append({'type': 'Amendment Identifier', 'value': self._title_page['amendment_identifier']})    
    
    # Amendment Scope - Part of Amendment
    x = self._title_page['amendment_scope']
    
    # Compound Codes - No implementation details currently
    x = self._title_page['compound_codes']
    
    # Compound Names - No implementation details currently
    x = self._title_page['compound_names']
    
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
    sponsor = self._sponsor()
    org = self._organization_from_organization(sponsor)
    if org:
      self._entries.append({'item': self._organization_from_organization(sponsor), 'url': 'https://www.example.com/Composition/1234'})
      item = self._associated_party_reference(f"Organization/{org.id}", 'sponsor', 'sponsor')
      if item:
        result.associatedParty.append(item)

    # Manufacturer Name and Address
    x = self._title_page['manufacturer_name_and_address']
    
    # Regulatory Agency Identifiers, see above
    x = self._title_page['regulatory_agency_identifiers']
    
    # Sponsor Approval
    status = self._progress_status(self._title_page['sponsor_approval_date'], 'sponsor-approved', 'sponsor apporval date')
    if status:
      result.progressStatus.append(status)
    
    # Sponsor Signatory
    item = self._associated_party(self._title_page['sponsor_signatory'], 'sponsor-signatory', 'sponsor signatory')
    if item:
      result.associatedParty.append(item)
    
    # Medical Expert Contact
    item = self._associated_party(self._title_page['medical_expert_contact'], 'medical-expert', 'medical expert')
    if item:
      result.associatedParty.append(item)
    
    # SAE Reporting Method
    ext = self._extension("research-study-sae-reporting-method", self._title_page['sae_reporting_method'])
    if ext:
      result.extension.append(ext)
    
    # Amendment
    ext = self._amendment_ext(version)
    if ext:
      result.extension.append(ext)

    print(f"RESEARCH STUDY: {result}")
    return result
  
  def _sponsor_identifier(self):
    for identifier in self.study_version.studyIdentifiers:
      if identifier.studyIdentifierScope.organizationType.code == 'C70793':
        return identifier
    return None

  def _sponsor(self):
    for identifier in self.study_version.studyIdentifiers:
      if identifier.studyIdentifierScope.organizationType.code == 'C70793':
        return identifier.studyIdentifierScope
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

  def _codeable_concept(self, code: Coding):
    return CodeableConcept(coding=[code])
  
  def _organization_from_organization(self, organization: USDMOrganization):
    print(f"ORG: {organization}")
    address = self._address_from_address(organization.legalAddress)
    name = organization.label if organization.label else organization.name
    return Organization(id=str(uuid4()), name=name, contact=[{'address': address}])

  def _address_from_address(self, address: USDMAddress):  
    x = dict(address)
    x.pop('instanceType')
    y = {}
    for k, v in x.items():
      if v:
        y[k] = v
    if 'line' in y:
      y['line'] = [y['line']]
    if 'country' in y:
      y['country'] = address.country.decode
    result = AddressType(y)
    print(f"ADDRESS: {result}")
    return result

  def _associated_party(self, value: str, role_code: str, role_display: str):
    if value:
      code = Coding(system='http://hl7.org/fhir/research-study-party-role', code=role_code, display=role_display)
      role = CodeableConcept(coding=[code])
      return ResearchStudyAssociatedParty(role=role, party={'display': value})
    else:
      return None

  def _associated_party_reference(self, reference: str, role_code: str, role_display: str):
    if reference:
      code = Coding(system='http://hl7.org/fhir/research-study-party-role', code=role_code, display=role_display)
      role = CodeableConcept(coding=[code])
      return ResearchStudyAssociatedParty(role=role, party={'reference': reference})
    else:
      return None

  def _progress_status(self, value: str, state_code: str, state_display: str):
    print(f"DATE: {value}")
    if value:
      code = Coding(system='http://hl7.org/fhir/research-study-party-role', code=state_code, display=state_display)
      state = CodeableConcept(coding=[code])
      return ResearchStudyProgressStatus(state=state, period={'start': value})
    else:
      return None

  def _amendment_ext(self, version: USDMStudyVersion):
    source = version.amendments[0]
    amendment = Extension(url=f"http://hl7.org/fhir/uv/ebm/StructureDefinition/studyAmendment", extension=[])
    ext = self._extension('amendmentNumber', value=self._title_page['amendment_identifier'])
    if ext:
      amendment.extension.append(ext)
    ext = self._extension('scope', value=self._title_page['amendment_scope'])
    if ext:
      amendment.extension.append(ext)
    ext = self._extension('details', value=self._title_page['amendment_details'])
    if ext:
      amendment.extension.append(ext)
    ext = self._extension_boolean('substantialImpactSafety', value=self._amendment['safety_impact'])
    if ext:
      amendment.extension.append(ext)
    ext = self._extension('substantialImpactSafety', value=self._amendment['safety_impact_reason'])
    if ext:
      amendment.extension.append(ext)
    ext = self._extension_boolean('substantialImpactSafety', value=self._amendment['robustness_impact'])
    if ext:
      amendment.extension.append(ext)
    ext = self._extension('substantialImpactSafety', value=self._amendment['robustness_impact_reason'])
    if ext:
      amendment.extension.append(ext)

    primary = self._codeable_concept(self._coding_from_code(source.primaryReason.code))
    ext = self._extension_codeable('primaryReason', value=primary)
    if ext:
      amendment.extension.append(ext)
      secondary = self._codeable_concept(self._coding_from_code(source.secondaryReasons[0].code))
      ext = self._extension_codeable('secondaryReason', value=secondary)
      if ext:
        amendment.extension.append(ext)
    return amendment
  
  def _extension(self, key: str, value: str):
    return Extension(url=f"http://hl7.org/fhir/uv/ebm/StructureDefinition/{key}", valueString=value) if value else None

  def _extension_boolean(self, key: str, value: str):
    return Extension(url=f"http://hl7.org/fhir/uv/ebm/StructureDefinition/{key}", valueBoolean=value) if value else None

  def _extension_codeable(self, key: str, value: CodeableConcept):
    return Extension(url=f"http://hl7.org/fhir/uv/ebm/StructureDefinition/{key}", valueCodeableConcept=value) if value else None
