from fhir.resources.coding import Coding
from usdm_model.code import Code as USDMCode

class CodingFactory():

  def __init__(self, code: USDMCode):
    try:
      self.item = Coding(system=code.codeSystem, version=code.codeSystemVersion, code=code.code, display=code.decode)
    except Exception as e:
      self.item = None
