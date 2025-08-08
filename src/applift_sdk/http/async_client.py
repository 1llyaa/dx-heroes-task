import httpx
from typing import Optional, Dict, Any

from applift_sdk.auth import AsyncTokenManager


class AsyncBaseClient:
    """
    Base async HTTP client that handles auth and sends requests to the API.
    """

    def __init__(self, base_url: str, token_manager: AsyncTokenManager):
        self._base_url = base_url
        self._token_manager = token_manager
        self._client = httpx.AsyncClient(base_url=base_url)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    async def _request(
            self,
            method: str,
            endpoint: str,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Sends an authenticated HTTP request.
        """
        token = await self._token_manager.get_access_token()
        auth_headers = {"Authorization": f"Bearer {token}"}
        if headers:
            auth_headers.update(headers)

        response = await self._client.request(
            method=method,
            url=endpoint,
            headers=auth_headers,
            params=params,
            json=json,
        )

        response.raise_for_status()
        return response

    async def aclose(self):
        """
        Close the internal HTTPX client.
        """
        await self._client.aclose()
