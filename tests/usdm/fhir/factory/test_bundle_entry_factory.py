from fhir.resources.researchstudy import ResearchStudy
from app.usdm.fhir.factory.bundle_entry_factory import BundleEntryFactory
from tests.usdm.fhir.factory.dict_result import DictResult

def test_bundle_entry():
  resource = ResearchStudy(status='draft', identifier=[], extension=[], label=[], associatedParty=[], progressStatus=[], objective=[], comparisonGroup=[], outcomeMeasure=[])
  params = {'resource': resource, 'fullUrl': 'http://example.com/url'}
  expected = {
    'extension': None,
    'fhir_comments': None,
    'fullUrl': 'http://example.com/url',
    'fullUrl__ext': None,
    'id': None,
    'link': None,
    'modifierExtension': None,
    'request': None,
    'resource': {
      'associatedParty': [],
      'classifier': None,
      'comparisonGroup': [],
      'condition': None,
      'contained': None,
      'date': None,
      'date__ext': None,
      'description': None,
      'descriptionSummary': None,
      'descriptionSummary__ext': None,
      'description__ext': None,
      'extension': [],
      'fhir_comments': None,
      'focus': None,
      'id': None,
      'identifier': [],
      'implicitRules': None,
      'implicitRules__ext': None,
      'keyword': None,
      'label': [],
      'language': None,
      'language__ext': None,
      'meta': None,
      'modifierExtension': None,
      'name': None,
      'name__ext': None,
      'note': None,
      'objective': [],
      'outcomeMeasure': [],
      'partOf': None,
      'period': None,
      'phase': None,
      'primaryPurposeType': None,
      'progressStatus': [],
      'protocol': None,
      'recruitment': None,
      'region': None,
      'relatedArtifact': None,
      'resource_type': 'ResearchStudy',
      'result': None,
      'site': None,
      'status': 'draft',
      'status__ext': None,
      'studyDesign': None,
      'text': None,
      'title': None,
      'title__ext': None,
      'url': None,
      'url__ext': None,
      'version': None,
      'version__ext': None,
      'whyStopped': None,
    },
    'resource_type': 'BundleEntry',
    'response': None,
    'search': None
  }
  result = BundleEntryFactory(**params)
  assert result.item is not None
  assert DictResult(result.item).result == expected

def test_bundle_entry_error():
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = BundleEntryFactory(**params)
  assert result.item is None

