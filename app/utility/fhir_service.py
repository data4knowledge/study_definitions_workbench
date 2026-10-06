import httpx

from app.utility.service import Service


class FHIRService(Service):
    """FHIR server client.

    ``auth`` is an optional ``(username, password)`` pair sent as basic auth
    on PUT. Only the configured default server is given credentials; user
    endpoints are created without them so credentials never leak to servers
    users add themselves.
    """

    def __init__(self, url, auth: tuple[str, str] | None = None):
        super().__init__(base_url=url)
        self._auth = auth

    def bundle_list(self):
        return super().get("Bundle")

    def get(self, url):
        return super().get(url)

    def post(self, url, data="", timeout=None):
        return super().post(url, data, timeout)

    async def put(self, url, data={}, timeout=None):
        try:
            headers = {"Content-Type": "application/json"}
            timeout = timeout if timeout else self.DEFAULT_TIMEOUT
            kwargs = {"data": data, "timeout": timeout, "headers": headers}
            if self._auth:
                kwargs["auth"] = self._auth
            response = await self._client.put(self._full_url(url), **kwargs)
            return (
                self._success(response)
                if response.status_code in [200, 201]
                else self._failure("PUT", response)
            )
        except httpx.HTTPError as e:
            return self._exception("PUT", e)
