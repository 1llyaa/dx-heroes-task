import httpx
from typing import Optional, Dict, Any

from applifting_sdk.auth import AsyncTokenManager
from applifting_sdk.helpers.uuid_serializer import _to_jsonable
from applifting_sdk.exceptions import AuthenticationError, NotFoundError, ConflictError, ValidationError
from applifting_sdk.config import settings


class AsyncBaseClient:
    """
    Base async HTTP client that handles auth and sends requests to the API.
    """

    def __init__(self, token_manager: AsyncTokenManager):
        self._base_url = settings.base_url
        self._token_manager = token_manager
        self._client = httpx.AsyncClient(base_url=self._base_url)

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
        auth_headers = {"Bearer": token}
        if headers:
            auth_headers.update(headers)

        if json:
            json = _to_jsonable(json)

        response = await self._client.request(
            method=method,
            url=endpoint,
            headers=auth_headers,
            params=params,
            json=json,
        )

        if response.status_code == 401:
            raise AuthenticationError(response.text)
        elif response.status_code == 404:
            raise NotFoundError(response.text)
        elif response.status_code == 409:
            raise ConflictError(response.text)
        elif response.status_code == 422:
            raise ValidationError(response.text)
        response.raise_for_status()

        return response

    async def aclose(self):
        """
        Close the internal HTTPX client.
        """
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
