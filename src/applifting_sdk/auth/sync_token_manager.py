import os
import time
import json
import threading
from typing import Optional

import requests
from platformdirs import user_cache_dir

from applifting_sdk.helpers import ErrorHandler
from applifting_sdk.models import AuthResponse
from applifting_sdk.exceptions import (
    AppliftingSDKError,
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
)
from applifting_sdk.config import settings


class SyncTokenManager:
    """
    Manages JWT access tokens for authenticated requests.
    Automatically refreshes token if expired.
    Synchronous version using requests and threading.Lock.
    """

    def __init__(self, refresh_token: str):
        self._refresh_token: str = refresh_token
        self._base_url: str = settings.base_url
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._lock: threading.Lock = threading.Lock()
        self._expiration_seconds: int = settings.token_expiration_seconds
        self._buffer_seconds: int = settings.token_expiration_buffer_seconds
        self._error_handler: ErrorHandler = ErrorHandler()

        # Cache location
        cache_dir: str = user_cache_dir("applifting_sdk", "AppliftingSDK")
        os.makedirs(cache_dir, exist_ok=True)
        self._cache_file_path: str = os.path.join(cache_dir, "token_cache.json")

    def get_access_token(self) -> str:
        with self._lock:
            # Check cache first
            if self._access_token and not self._is_token_expired():
                return self._access_token

            cached_token: str | None = self._read_token_cache()
            if cached_token and not self._is_token_expired():
                self._access_token: str = cached_token
                return self._access_token

            # Refresh token
            self._refresh_token_request()
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

    def _refresh_token_request(self):
        if not self._refresh_token:
            raise AppliftingSDKError("No refresh token was provided")

        try:
            response: requests.Response = requests.post(
                f"{self._base_url}/api/v1/auth",
                headers={"Bearer": self._refresh_token},
            )

        except requests.exceptions.ConnectTimeout as e:
            raise AppliftingSDKTimeoutError("Connection timed out") from e
        except requests.exceptions.ReadTimeout as e:
            raise AppliftingSDKTimeoutError("Read timed out") from e
        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
            raise AppliftingSDKNetworkError(str(e)) from e

        if not response.ok:
            self._error_handler.raise_api_error(response)

        data = AuthResponse(**response.json())
        self._access_token = data.access_token
        self._token_expires_at = time.time() + self._expiration_seconds