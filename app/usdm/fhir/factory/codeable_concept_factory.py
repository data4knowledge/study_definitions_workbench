from fhir.resources.codeableconcept import CodeableConcept

class CodeableConceptFactory():

  def __init__(self, **kwargs):
    try:
      self.item = CodeableConcept(kwargs)
    except Exception as e:
      self.item = None
  