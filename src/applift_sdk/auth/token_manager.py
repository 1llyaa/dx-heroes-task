import time
import asyncio
import httpx

from typing import Optional
from applift_sdk.models import AuthResponse


class AsyncTokenManager:
    """
    Manages JWT access tokens for authenticated requests.
    Automatically refreshes token if expired.
    """

    def __init__(self, refresh_token: str, base_url: str):
        self._refresh_token = refresh_token
        self._base_url = base_url
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        """
        Returns a valid access token, refreshing it if necessary.
        """
        async with self._lock:
            if self._is_expired():
                await self._refresh_token_request()
            return self._access_token

    def _is_expired(self) -> bool:
        """
        Checks whether the current token has expired.
        """
        return time.time() >= self._token_expires_at

    async def _refresh_token_request(self):
        """
        Performs a token refresh request to the API.
        """
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.post(
                "/api/v1/auth",
                headers={"Bearer": self._refresh_token},
            )
            response.raise_for_status()
            data = AuthResponse(**response.json())
            self._access_token = data.access_token
            self._token_expires_at = time.time() + 300  # 5 minutes
