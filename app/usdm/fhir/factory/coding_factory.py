from fhir.resources.coding import Coding
from usdm_model.code import Code as USDMCode

class CodingFactory():

  def __init__(self, **kwargs):
    try:
      if 'usdm_code' in kwargs:
        kwargs['system'] = kwargs['code'].codeSystem, 
        kwargs['version'] = kwargs['code'].codeSystemVersion, 
        kwargs['code'] = kwargs['code'].code, 
        kwargs['display'] = kwargs['code'].decode
        kwargs.pop('usdm_code')
      self.item = Coding(kwargs)
    except Exception as e:
      self.item = None
