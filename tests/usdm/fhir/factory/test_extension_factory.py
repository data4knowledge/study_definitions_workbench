from app.usdm.fhir.factory.extension_factory import ExtensionFactory

def test_extension_string():
  params = {'url': 'amendmentNumber', 'valueString': 'something'}
  expected = _expected()
  expected['url'] = 'amendmentNumber'
  expected['valueString'] = 'something'
  result = ExtensionFactory(**params)
  assert result.item is not None
  assert result.item.__dict__ == expected

def test_extension_boolean():
  params = {'url': 'http://example.com/something', 'valueBoolean': 'true'}
  expected = _expected()
  expected['url'] = 'http://example.com/something'
  expected['valueBoolean'] = True
  result = ExtensionFactory(**params)
  assert result.item is not None
  assert result.item.__dict__ == expected

def test_extension_error(mocker, monkeypatch):
  params = {'valueString': (1,2)} # Force an exception, code not a string type
  result = ExtensionFactory(**params)
  assert result.item is None

def _expected():
  return {
    'id': None,
    'fhir_comments': None,
    'resource_type': 'Extension', 
    'url': None, 
    'extension': [], 
    'valueAddress': None,
    'valueAge': None,
    'valueAnnotation': None,
    'valueAttachment': None,
    'valueAvailability': None,
    'valueBase64Binary': None,
    'valueBoolean': None,
    'valueCanonical': None,
    'valueCode': None,
    'valueCodeableConcept': None,
    'valueCodeableReference': None,
    'valueCoding': None,
    'valueContactDetail': None,
    'valueContactPoint': None,
    'valueCount': None,
    'valueDataRequirement': None,
    'valueDate': None,
    'valueDateTime': None,
    'valueDecimal': None,
    'valueDistance': None,
    'valueDosage': None,
    'valueDuration': None,
    'valueExpression': None,
    'valueExtendedContactDetail': None,
    'valueHumanName': None,
    'valueId': None,
    'valueIdentifier': None,
    'valueInstant': None,
    'valueInteger': None,
    'valueInteger64': None,
    'valueMarkdown': None,
    'valueMeta': None,
    'valueMoney': None,
    'valueOid': None,
    'valueParameterDefinition': None,
    'valuePeriod': None,
    'valuePositiveInt': None,
    'valueQuantity': None,
    'valueRange': None,
    'valueRatio': None,
    'valueRatioRange': None,
    'valueReference': None,
    'valueRelatedArtifact': None,
    'valueSampledData': None,
    'valueSignature': None,
    'valueString': None,
    'valueTime': None,
    'valueTiming': None,
    'valueTriggerDefinition': None,
    'valueUnsignedInt': None,
    'valueUri': None,
    'valueUrl': None,
    'valueUuid': None,
    'valueUsageContext': None,
  }
