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
      headers = {"Content-Type":"application/json"}
      response = await self._client.get(self._full_url(url), headers=headers)
      return self._success(response) if response.status_code == 200 else self._failure('GET', response)
    except httpx.HTTPError as e:
      return self._exception("GET", e)

  async def file_post(self, url, files, data={}):
    try:
      full_url = self._full_url(url)
      response = await self._client.post(full_url, files=files, data=data) if data else await self._client.post(full_url, files=files)
      return self._success(response) if response.status_code in [200, 201] else self._failure('POST', response)
    except httpx.HTTPError as e:
      return self._exception("POST (file)", e)

  async def post(self, url, data={}, timeout=None):
    try:
      headers = {"Content-Type":"application/json"}
      timeout = timeout if timeout else self.DEFAULT_TIMEOUT
      response = await self._client.post(self._full_url(url), data=data, timeout=timeout, headers=headers)       
      return self._success(response) if response.status_code in [200, 201] else self._failure('POST', response)
    except httpx.HTTPError as e:
      return self._exception("POST", e)

  async def delete(self, url, data={}):
    try:
      headers = {"Content-Type":"application/json"}
      response = await self._client.delete(self._full_url(url), headers=headers)       
      return self._success(response) if response.status_code == 204 else self._failure('DELETE', response)
    except httpx.HTTPError as e:
      return self._exception("DELETE", e)

  def _success(self, response):
    return self._response(True, response.status_code, json.loads(response.text))
    
  def _failure(self, operation, response):
    message = f"An error occurred performing the '{operation}'. Error: '{response.text}'"
    return self._response(False, response.status_code, {} ,message)
    
  def _exception(self, operation, e):
    application_logger.exception(message, e)
    message = f"HTTPX '{operation}' operation raised exception {e.__class__.__name__}"
    return self._response(False, '', {}, message)

  def _response(self, success: bool, status: str, data: dict, message: str=''):
    application_logger.error(message)
    return {'success': success, 'status': status, 'data': data, 'message': message}

  def _full_url(self, url):
    return f"{self.base_url}{url}" if url.startswith("/") else f"{self.base_url}/{url}"