from typing import Literal, Optional, Union
from applifting_sdk.auth import AsyncTokenManager, SyncTokenManager
from applifting_sdk.http import AsyncBaseClient, SyncBaseClient
from applifting_sdk.resources import AsyncOffersAPI, AsyncProductsAPI, SyncOffersAPI, SyncProductsAPI

try:
    import httpx
except ImportError:
    httpx = None

try:
    import requests
except ImportError:
    requests = None

HttpBackend = Literal["httpx", "requests"]


class AppliftingSDKClient:
    def __init__(
            self,
            refresh_token: str,
            http_backend: Optional[HttpBackend] = None,
    ):
        self._token_manager: Union[AsyncTokenManager, SyncTokenManager]
        self._client: Union[AsyncBaseClient, SyncBaseClient]
        self.offers: Union[AsyncOffersAPI, SyncOffersAPI]
        self.products: Union[AsyncProductsAPI, SyncProductsAPI]

        # Auto-select backend
        if http_backend is None:
            if httpx:
                http_backend = "httpx"
            elif requests:
                http_backend = "requests"
            else:
                raise RuntimeError("Install httpx or requests: pip install httpx requests")

        # Validate backend
        if http_backend == "httpx" and not httpx:
            raise RuntimeError("httpx not installed: pip install httpx")
        if http_backend == "requests" and not requests:
            raise RuntimeError("requests not installed: pip install requests")

        self.backend = http_backend
        self.is_async = http_backend == "httpx"

        # Initialize based on backend
        if http_backend == "httpx":
            self._token_manager: AsyncTokenManager = AsyncTokenManager(refresh_token=refresh_token)
            self._client: AsyncBaseClient = AsyncBaseClient(token_manager=self._token_manager)
            self.offers: AsyncOffersAPI = AsyncOffersAPI(client=self._client)
            self.products: AsyncProductsAPI = AsyncProductsAPI(client=self._client)
        elif http_backend == "requests":
            self._token_manager: SyncTokenManager = SyncTokenManager(refresh_token=refresh_token)
            self._client: SyncBaseClient = SyncBaseClient(token_manager=self._token_manager)
            self.offers: SyncOffersAPI = SyncOffersAPI(client=self._client)
            self.products: SyncProductsAPI = SyncProductsAPI(client=self._client)

    # Context managers
    def __enter__(self):
        if self.is_async:
            raise RuntimeError("Use 'async with' for httpx backend")
        return self

    def __exit__(self, *args):
        self._client.close()

    async def __aenter__(self):
        if not self.is_async:
            raise RuntimeError("Use 'with' for requests backend")
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    # Cleanup
    def close(self):
        if self.is_async:
            raise RuntimeError("Use aclose() for httpx backend")
        self._client.close()

    async def aclose(self):
        if not self.is_async:
            raise RuntimeError("Use close() for requests backend")
        await self._client.aclose()