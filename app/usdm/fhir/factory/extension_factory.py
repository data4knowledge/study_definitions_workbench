from fhir.resources.extension import Extension

class ExtensionFactory():

  def __init__(self, **kwargs):
    try:
      kwargs['extension'] = []
      self.item = Extension(**kwargs)
    except Exception as e:
      self.item = None
  