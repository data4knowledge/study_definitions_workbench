# import warnings
# from bs4 import BeautifulSoup   
# from app.usdm.fhir.to_fhir import ToFHIR
# from fhir.resources.bundle import Bundle, BundleEntry
# from fhir.resources.identifier import Identifier
# from fhir.resources.composition import Composition
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
# from fhir.resources.reference import Reference
from fhir.resources.researchstudy import ResearchStudy
# from fhir.resources.extension import Extension
# from fhir.resources.researchstudy import ResearchStudyAssociatedParty
# from fhir.resources.researchstudy import ResearchStudyProgressStatus
# from fhir.resources.organization import Organization as FHIROrganization
# from fhir.resources.extendedcontactdetail import ExtendedContactDetail
from fhir.resources.fhirtypes import ResearchStudyLabelType, AddressType
# from fhir.resources.fhirprimitiveextension import FHIRPrimitiveExtension
# from fhir.resources.group import Group
# from usdm_model.code import Code as USDMCode
# #from usdm_model.study_title import StudyTitle as USDMStudyTitle
# from usdm_model.endpoint import Endpoint as USDMEndpoint
# #from usdm_model.estimand import Estimand as USDMEstimand
# from usdm_model.study_intervention import StudyIntervention as USDMStudyIntervention
# from usdm_model.governance_date import GovernanceDate as USDMGovernanceDate
# 
# from usdm_model.address import Address as USDMAddress
# from usdm_model.study_version import StudyVersion as USDMStudyVersion
# from usdm_model.study_design import StudyDesign as USDMStudyDesign
# from usdm_model.eligibility_criterion import EligibilityCriterion
# from uuid import uuid4
# from d4kms_generic import application_logger
# from app.usdm.model.v4.study_version import *
# from app.usdm.model.v4.study_identifier import *
# import datetime
from app.usdm.fhir.factory.extension_factory import ExtensionFactory
from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from app.usdm.fhir.factory.coding_factory import CodingFactory
from app.usdm.fhir.factory.organization_factory import OrganizationFactory
from app.usdm.fhir.factory.associated_party_factory import AssociatedPartyFactory
from app.usdm.fhir.factory.progress_status_factory import ProgressStatusFactory
from usdm_model.study import Study as USDMStudy
from usdm_model.study_version import StudyVersion as USDMStudyVersion

class ResearchStudyFactory:

  def __init__(self, study: USDMStudy):
    self._version: USDMStudyVersion = study.versions[0]
    self._organizations: dict = self._version.organization_map()

    # Base instance
    self.item = ResearchStudy(status='draft', identifier=[], extension=[], label=[], associatedParty=[], progressStatus=[], objective=[], comparisonGroup=[], outcomeMeasure=[])

    # Sponsor Confidentiality Statememt
    ext = ExtensionFactory({'url': "http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement", 'stringValue': self._title_page['sponsor_confidentiality']})
    if ext.item:
      self.item.extension.append(ext.item)
    
    # Full Title
    self.item.title = self._version.official_title() # self._get_title('Official Study Title').text
    
    # Trial Acronym
    acronym = self._version.acronym() # self._get_title('Study Acronym')
    if acronym:
      coding = CodingFactory(usdm_code=acronym.type)
      type = CodeableConceptFactory(coding=coding) 
      self.item.label.append(ResearchStudyLabelType(type=type, value=acronym.text))
    
    # Sponsor Protocol Identifier
    for identifier in self._version.studyIdentifiers:
      org = identifier.scoped_by(self._organizations)
      identifier_cc = CodeableConceptFactory({'text': org.type.decode})
      #print(f"IDENTIFIER: {identifier} = {identifier_code}")
      self.item.identifier.append({'type': identifier_cc.item, 'system': 'https://example.org/sponsor-identifier', 'value': identifier.text})
    
    # Original Protocol - No implementation details currently
    x = self._title_page['original_protocol']
    
    # Version Number
    self.item.version = self._version.versionIdentifier
    
    # Version Date
    approval_date = self._document_date()
    if approval_date:
      self.item.date = approval_date.dateValue
    
    # Amendment Identifier
    identifier_code = CodeableConceptFactory({'text': 'Amendment Identifier'})
    self.item.identifier.append({'type': identifier_code, 'system': 'https://example.org/amendment-identifier', 'value': self._title_page['amendment_identifier']})    
    
    # Amendment Scope - Part of Amendment
    
    # Compound Codes - No implementation details currently
    x = self._title_page['compound_codes']
    
    # Compound Names - No implementation details currently
    x = self._title_page['compound_names']
    
    # Trial Phase
    phase = self._version.phase()
    phase_code = Coding(system=phase.codeSystem, version=phase.codeSystemVersion, code=phase.code, display=phase.decode)
    self.item.phase = CodeableConcept(coding=[phase_code], text=phase.decode)
    
    # Short Title
    title = self._get_title('Brief Study Title')
    if title:
      type = CodeableConcept(coding=[self._coding_from_code(title.type)]) 
      self.item.label.append(ResearchStudyLabelType(type=type, value=title.text))    
    
    # Sponsor Name and Address
    sponsor = self._version.sponsor()
    org = OrganizationFactory(sponsor)
    if org:
      self._entries.append({'item': org, 'url': 'https://www.example.com/Composition/1234D'})
      item = AssociatedPartyFactory(party={'reference': f"Organization/{self._fix_id(org.id)}"}, role='sponsor', code='sponsor')
      if item:
        self.item.associatedParty.append(item)

    # Manufacturer Name and Address
    x = self._title_page['manufacturer_name_and_address']
    
    # Regulatory Agency Identifiers, see above
    x = self._title_page['regulatory_agency_identifiers']
    
    # Sponsor Approval
    status = ProgressStatusFactory(self._title_page['sponsor_approval_date'], 'sponsor-approved', 'sponsor apporval date')
    if status:
      self.item.progressStatus.append(status)
    
    # Sponsor Signatory
    item = AssociatedPartyFactory(party={'value': self._title_page['sponsor_signatory']}, role='sponsor-signatory', code='sponsor signatory')
    if item:
      self.item.associatedParty.append(item)
    
    # Medical Expert Contact
    item = AssociatedPartyFactory(party={'value': self._title_page['medical_expert_contact']}, role='medical-expert', code='medical-expert')
    if item:
      self.item.associatedParty.append(item)
    
    # # SAE Reporting Method
    # ext = self._extension_string("http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sae-reporting-method", self._title_page['sae_reporting_method'])
    # if ext:
    #   self.item.extension.append(ext)
    
    # # Amendment
    # ext = self._amendment_ext(version)
    # if ext:
    #   self.item.extension.append(ext)

    # # Objectives
    # self._estimands(result)

    # # Recruitment
    # self._recruitment(result, group_id)

    # #print(f"RESEARCH STUDY: {result}")
    # return result
  
