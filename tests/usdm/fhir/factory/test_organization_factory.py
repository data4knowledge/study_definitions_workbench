from app.usdm.fhir.factory.organization_factory import OrganizationFactory
from usdm_model.organization import Organization
from tests.usdm.fhir.factory.dict_result import DictResult
from tests.mocks.fhir_factory_mocks import mock_handle_exception
from tests.mocks.general_mocks import mock_called

def test_organization():
  org = {
    "id": "Org_1", 
    "name": "ClinicalTrials.gov", 
    "label": "", 
    "type": {"id": "Code_1", "code": "C93453", "codeSystem": "http://www.cdisc.org", "codeSystemVersion": "2023-12-15", "decode": "Study Registry", "instanceType": "Code"},
    "identifierScheme": "USGOV", "identifier": "CT-GOV",
    "legalAddress": {
      "id": "Addr_1", "text": "line, city, district, state, postal_code, Denmark", "lines": ["line"], "city": "city", "district": "district", "state": "state", "postalCode": "postal_code",
      "country": {"id": "Code_2", "code": "DNK", "codeSystem": "ISO 3166 1 alpha3", "codeSystemVersion": "2020-08", "decode": "Denmark", "instanceType": "Code"},
      "instanceType": "Address"},
    "managedSites": [],
    "instanceType": "Organization"
  }
  org = Organization(**org)
  expected = _expected()
  result = OrganizationFactory(org)
  assert result.item is not None
  result_dict = DictResult(result.item).result
  expected['id'] = result_dict['id']
  assert result_dict == expected

def test_organization_error(mocker):
  he = mock_handle_exception(mocker)
  result = OrganizationFactory(None)
  assert result.item is None
  assert mock_called(he)

def _expected():
  return {
    'id': '0fe821f3-4fbe-4946-9d3e-9630c1cbaf0c',
    'contact': [
      {
        'address': {
          'id': 'Addr_1',
          'city': 'city',
          'country': 'Denmark',
          'district': 'district',
          'postalCode': 'postal_code',
          'state': 'state',
          'text': 'line, city, district, state, postal_code, Denmark',
        },
      }
    ],
    'name': 'ClinicalTrials.gov',
    'resourceType': 'Organization'
  }