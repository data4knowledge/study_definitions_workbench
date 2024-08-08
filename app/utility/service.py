import httpx
import json
from d4kms_generic.logger import application_logger

class Service():

  DEFAULT_TIMEOUT = 5.0

  def __init__(self, base_url):
    self.base_url = base_url[:-1] if base_url.endswith("/") else base_url
    self._client = httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT)
    
  async def status(self):
    return await self.get(self.base_url)

  async def get(self, url):
    try:
      response = await self._client.get(self._full_url(url))
      return json.loads(response.text) if response.status_code == 200 else self._bad_response(response)
    except httpx.HTTPError as e:
      return self._exception("GET", e)

  async def file_post(self, url, files, data={}):
    try:
      full_url = self._full_url(url)
      response = await self._client.post(full_url, files=files, data=data) if data else await self._client.post(full_url, files=files)
      return json.loads(response.text) if response.status_code in [200, 201] else self._bad_response(response)
    except httpx.HTTPError as e:
      return self._exception("POST (file)", e)

  async def post(self, url, data={}, timeout=None):
    try:
      timeout = timeout if timeout else self.DEFAULT_TIMEOUT
      response = await self._client.post(self._full_url(url), json=data, timeout=timeout)       
      return json.loads(response.text) if response.status_code in [200, 201] else self._bad_response(response)
    except httpx.HTTPError as e:
      return self._exception("POST", e)

  async def delete(self, url, data={}):
    try:
      response = await self._client.delete(self._full_url(url))       
      return {} if response.status_code == 204 else self._bad_response(response)
    except httpx.HTTPError as e:
      return self._exception("DELETE", e)

  def _bad_response(self, response):
    return self._error(f"Service failed to respond. Error: '{response.text}', status: {response.status_code}")
    
  def _error(self, message):
    application_logger.error(message)
    return {'error': message}

  def _exception(self, operation, e):
    message = f"HTTPX '{operation}' operation raised exception {e.__class__.__name__}"
    application_logger.exception(message, e)
    return {'error': f"{message}"}

  def _full_url(self, url):
    return f"{self.base_url}{url}" if url.startswith("/") else f"{self.base_url}/{url}"