import httpx
from app.utility.service import Service
from d4k_ms_base.service_environment import ServiceEnvironment
# from d4kms_generic.service import Service


class FHIRService(Service):
    def __init__(self, url):
        super().__init__(base_url=url)
        self._se = ServiceEnvironment()

    def bundle_list(self):
        return super().get("Bundle")

    def get(self, url):
        return super().get(url)

    def post(self, url, data="", timeout=None):
        return super().post(url, data, timeout)

    async def put(self, url, data={}, timeout=None):
        try:
            username = self._se.get("ENDPOINT_USERNAME")
            password = self._se.get("ENDPOINT_PASSWORD")
            headers = {"Content-Type": "application/json"}
            timeout = timeout if timeout else self.DEFAULT_TIMEOUT
            response = await self._client.put(
                self._full_url(url),
                data=data,
                timeout=timeout,
                headers=headers,
                auth=(username, password),
            )
            return (
                self._success(response)
                if response.status_code in [200, 201]
                else self._failure("PUT", response)
            )
        except httpx.HTTPError as e:
            return self._exception("PUT", e)
