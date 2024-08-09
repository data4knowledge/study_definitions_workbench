#from app.utility.service import Service
from d4kms_generic.service import Service

class FHIRService(Service):

  def __init__(self, url):
    super().__init__(base_url=url)

  def bundle_list(self):
    return super().get('Bundle')

  def get(self, url):
    return super().get(url)

  def post(self, url, data={}, timeout=None):
    return super().post(url, data, timeout)