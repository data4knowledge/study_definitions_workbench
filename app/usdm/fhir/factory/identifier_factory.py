import traceback

from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.identifier import Identifier

class IdentifierFactory(BaseFactory):
  
  def __init__(self, **kwargs):
    try: 
      self.item = Identifier(**kwargs)
    except Exception as e:
      print(f"ID EXCEPTION: {e}\n{traceback.format_exc()}")
      self.item = None
