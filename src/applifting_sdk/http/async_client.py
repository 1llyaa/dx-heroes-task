import httpx
from typing import Optional, Dict, Any

from applifting_sdk.auth import AsyncTokenManager
from applifting_sdk.helpers.uuid_serializer import _to_jsonable
from applifting_sdk.exceptions import AppliftingSDKNetworkError, AppliftingSDKTimeoutError, AuthenticationError, \
    PermissionDenied, NotFoundError, ConflictError, ValidationFailed, RateLimitError, ServerError, APIError

from applifting_sdk.config import settings
from applifting_sdk.models.validation import HTTPValidationError


class AsyncBaseClient:
    """
    Base async HTTP client that handles auth and sends requests to the API.
    """

    def __init__(self, token_manager: AsyncTokenManager):
        self._base_url: str = settings.base_url
        self._token_manager: AsyncTokenManager = token_manager
        self._client: httpx.AsyncClient = httpx.AsyncClient(base_url=self._base_url)

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
            json = _to_jsonable(json)

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

        if 200 <= response.status_code < 300:
            return response

        payload: dict | None = None
        text: str | None = None
        try:
            payload: dict = response.json()
        except Exception:
            try:
                text: str = response.text
            except Exception:
                text = None

        status: int = response.status_code

        if status == 401:
            raise AuthenticationError(status, "Unauthorized", details=payload, response_text=text)
        elif status == 403:
            raise PermissionDenied(status, "Forbidden", details=payload, response_text=text)
        elif status == 404:
            raise NotFoundError(status, "Not Found", details=payload, response_text=text)
        elif status == 409:
            raise ConflictError(status, "Conflict", details=payload, response_text=text)
        elif status == 422:
            details: HTTPValidationError | None = None
            if payload is not None:
                details: HTTPValidationError = HTTPValidationError(**payload)
            raise ValidationFailed(status, "Validation failed", details=details, response_text=text)
        elif status == 429:
            raise RateLimitError(status, "Too Many Requests", details=payload, response_text=text)
        elif 500 <= status < 600:
            raise ServerError(status, "Server error", details=payload, response_text=text)
        else:
            raise APIError(status, "Unexpected API error", details=payload, response_text=text)

    async def aclose(self):
        """
        Close the internal HTTPX client.
        """
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
