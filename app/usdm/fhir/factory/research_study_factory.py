from usdm_model.study import Study as USDMStudy
from usdm_model.study_version import StudyVersion as USDMStudyVersion
from fhir.resources.researchstudy import ResearchStudy
from app.usdm.fhir.factory.extension_factory import ExtensionFactory
from app.usdm.fhir.factory.codeable_concept_factory import CodeableConceptFactory
from app.usdm.fhir.factory.coding_factory import CodingFactory
from app.usdm.fhir.factory.organization_factory import OrganizationFactory
from app.usdm.fhir.factory.associated_party_factory import AssociatedPartyFactory
from app.usdm.fhir.factory.progress_status_factory import ProgressStatusFactory
from app.usdm.fhir.factory.label_type_factory import LabelTypeFactory

class ResearchStudyFactory:

  def __init__(self, study: USDMStudy):
    try:
      self._version: USDMStudyVersion = study.versions[0]
      self._organizations: dict = self._version.organization_map()

      # Base instance
      self.item = ResearchStudy(status='draft', identifier=[], extension=[], label=[], associatedParty=[], progressStatus=[], objective=[], comparisonGroup=[], outcomeMeasure=[])

      # Sponsor Confidentiality Statememt
      ext = ExtensionFactory({'url': "http://hl7.org/fhir/uv/ebm/StructureDefinition/research-study-sponsor-confidentiality-statement", 'stringValue': self._title_page['sponsor_confidentiality']})
      self.item.extension.append(ext.item)
      
      # Full Title
      self.item.title = self._version.official_title() # self._get_title('Official Study Title').text
      
      # Trial Acronym
      acronym = self._version.acronym() # self._get_title('Study Acronym')
      self.item.label.append(LabelTypeFactory(usdm_code=acronym.type, text=acronym.text))

      # Sponsor Protocol Identifier
      for identifier in self._version.studyIdentifiers:
        org = identifier.scoped_by(self._organizations)
        identifier_cc = CodeableConceptFactory({'text': org.type.decode})
        self.item.identifier.append({'type': identifier_cc.item, 'system': 'https://example.org/sponsor-identifier', 'value': identifier.text})
      
      # Original Protocol - No implementation details currently
      x = self._title_page['original_protocol']
      
      # Version Number
      self.item.version = self._version.versionIdentifier
      
      # Version Date
      approval_date = self._document_date()
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
      phase_code = CodingFactory(system=phase.codeSystem, version=phase.codeSystemVersion, code=phase.code, display=phase.decode)
      self.item.phase = CodeableConceptFactory(coding=[phase_code], text=phase.decode)
      
      # Short Title
      title = self._version.short_title() # self._get_title('Brief Study Title')
      self.item.label.append(LabelTypeFactory(usdm_code=title.type, text=title.text))
    
      # Sponsor Name and Address
      sponsor = self._version.sponsor()
      org = OrganizationFactory(sponsor)
      self._entries.append({'item': org, 'url': 'https://www.example.com/Composition/1234D'})
      item = AssociatedPartyFactory(party={'reference': f"Organization/{self._fix_id(org.id)}"}, role='sponsor', code='sponsor')
      self.item.associatedParty.append(item)

      # Manufacturer Name and Address
      x = self._title_page['manufacturer_name_and_address']
      
      # Regulatory Agency Identifiers, see above
      x = self._title_page['regulatory_agency_identifiers']
      
      # Sponsor Approval
      status = ProgressStatusFactory(self._title_page['sponsor_approval_date'], 'sponsor-approved', 'sponsor apporval date')
      self.item.progressStatus.append(status)
      
      # Sponsor Signatory
      item = AssociatedPartyFactory(party={'value': self._title_page['sponsor_signatory']}, role='sponsor-signatory', code='sponsor signatory')
      self.item.associatedParty.append(item)
      
      # Medical Expert Contact
      item = AssociatedPartyFactory(party={'value': self._title_page['medical_expert_contact']}, role='medical-expert', code='medical-expert')
      self.item.associatedParty.append(item)
      
    except Exception as e:
      self.item = None    
