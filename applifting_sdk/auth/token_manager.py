import os
import time
import json
import asyncio

import httpx
from typing import Optional
from platformdirs import user_cache_dir

from applifting_sdk.models import AuthResponse
from applifting_sdk.exceptions import (
    AppliftingSDKError,
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
    AuthenticationError,
    PermissionDenied,
    NotFoundError,
    ConflictError,
    ValidationFailed,
    RateLimitError,
    ServerError,
    APIError,
    BadRequestError,
)
from applifting_sdk.config import settings
from applifting_sdk.models.validation import HTTPValidationError


class AsyncTokenManager:
    """
    Manages JWT access tokens for authenticated requests.
    Automatically refreshes token if expired.
    """

    def __init__(
        self,
        refresh_token: str,
    ):
        self._refresh_token: str = refresh_token
        self._base_url: str = settings.base_url
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._lock: asyncio.Lock = asyncio.Lock()
        self._expiration_seconds: int = settings.token_expiration_seconds
        self._buffer_seconds: int = settings.token_expiration_buffer_seconds

        # Cache location
        cache_dir: str = user_cache_dir("applifting_sdk", "AppliftingSDK")
        os.makedirs(cache_dir, exist_ok=True)
        self._cache_file_path: str = os.path.join(cache_dir, "token_cache.json")

    async def get_access_token(self) -> str:
        async with self._lock:
            # Check cache first
            if self._access_token and not self._is_token_expired():
                return self._access_token

            cached_token: str | None = self._read_token_cache()
            if cached_token and not self._is_token_expired():
                self._access_token: str = cached_token
                return self._access_token

            # Refresh token
            await self._refresh_token_request()
            self._write_token_cache(self._access_token)
            return self._access_token

    def _is_token_expired(self) -> bool:
        return time.time() > (self._token_expires_at - self._buffer_seconds)

    def _read_token_cache(self) -> Optional[str]:
        if os.path.exists(self._cache_file_path):
            try:
                with open(self._cache_file_path, "r") as f:
                    data = json.load(f)
                    self._token_expires_at = data.get("expires_at", 0)
                    return data.get("access_token")
            except (OSError, json.JSONDecodeError):
                return None
        return None

    def _write_token_cache(self, token: str):

        with open(self._cache_file_path, "w") as f:
            json.dump(
                {
                    "access_token": token,
                    "expires_at": self._token_expires_at,
                },
                fp=f,
            )

    async def _refresh_token_request(self):
        async with httpx.AsyncClient(base_url=self._base_url) as client:

            if not self._refresh_token:
                raise AppliftingSDKError("No refresh token was provided - create .env file and use load_dotenv()")

            try:
                response: httpx.Response = await client.post(
                    "/api/v1/auth",
                    headers={"Bearer": self._refresh_token},
                )

            except httpx.ConnectTimeout as e:
                raise AppliftingSDKTimeoutError("Connection timed out") from e
            except httpx.ReadTimeout as e:
                raise AppliftingSDKTimeoutError("Read timed out") from e
            except (httpx.NetworkError, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                raise AppliftingSDKNetworkError(str(e)) from e

            if 200 <= response.status_code < 300:
                data = AuthResponse(**response.json())
                self._access_token = data.access_token
                self._token_expires_at = time.time() + self._expiration_seconds
                return

        payload: dict | None = None
        text: str | None = None
        # TODO - Improve logic here
        try:
            payload: dict = response.json()
        except Exception:
            try:
                text: str = response.text
            except Exception:
                text = None

        status: int = response.status_code

        if status == 400:
            raise BadRequestError(status, "Bad Request", details=payload, response_text=text)
        elif status == 401:
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
