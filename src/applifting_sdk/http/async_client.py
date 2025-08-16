import httpx
from typing import Optional, Dict, Any

from applifting_sdk.auth import AsyncTokenManager
from applifting_sdk.helpers import JSONSerializer, ErrorHandler
from applifting_sdk.exceptions import (
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
)

from applifting_sdk.config import settings


class AsyncBaseClient:
    """
    Base async HTTP client that handles auth and sends requests to the API.
    """

    def __init__(self, token_manager: AsyncTokenManager):
        self._base_url: str = settings.base_url
        self._token_manager: AsyncTokenManager = token_manager
        self._client: httpx.AsyncClient = httpx.AsyncClient(base_url=self._base_url)
        self.error_handler: ErrorHandler = ErrorHandler()
        self.json_serializer: JSONSerializer = JSONSerializer()

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Sends an authenticated HTTP request.
        """
        token: str = await self._token_manager.get_access_token()
        auth_headers: dict = {"Bearer": token}
        if headers:
            auth_headers.update(headers)

        if json:
            json = self.json_serializer.to_jsonable(json)

        try:
            response: httpx.Response = await self._client.request(
                method=method,
                url=endpoint,
                headers=auth_headers,
                params=params,
                json=json,
            )

        except httpx.ConnectTimeout as e:
            raise AppliftingSDKTimeoutError("Connection timed out") from e
        except httpx.ReadTimeout as e:
            raise AppliftingSDKTimeoutError("Read timed out") from e
        except (httpx.NetworkError, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            raise AppliftingSDKNetworkError(str(e)) from e

        if not response.is_success:
            self.error_handler.raise_api_error(response)

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
