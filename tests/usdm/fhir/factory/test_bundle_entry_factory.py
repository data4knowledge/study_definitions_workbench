from fhir.resources.researchstudy import ResearchStudy
from app.usdm.fhir.factory.bundle_entry_factory import BundleEntryFactory
from tests.usdm.fhir.factory.dict_result import DictResult

def test_bundle_entry():
  resource = ResearchStudy(status='draft', identifier=[], extension=[], label=[], associatedParty=[], progressStatus=[], objective=[], comparisonGroup=[], outcomeMeasure=[])
  params = {'resource': resource, 'fullUrl': 'http://example.com/url'}
  expected = {
    'fullUrl': 'http://example.com/url',
    'resource': {
      'resourceType': 'ResearchStudy',
      'status': 'draft',
    },
  }
  result = BundleEntryFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_bundle_entry_error():
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = BundleEntryFactory(**params)
  assert result.item is None

