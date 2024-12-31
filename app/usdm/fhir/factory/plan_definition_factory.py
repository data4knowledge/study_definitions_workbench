import traceback

from app.usdm.fhir.factory.base_factory import BaseFactory
from fhir.resources.plandefinition import PlanDefinition

class PlanDefinitionFactory(BaseFactory):
  
  def __init__(self, **kwargs):
    try: 
      self.item = PlanDefinition(**kwargs)
    except Exception as e:
      print(f"PD EXCEPTION: {e}\n{traceback.format_exc()}")
      self.item = None
