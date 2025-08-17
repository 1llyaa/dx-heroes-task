from applifting_sdk.auth import AsyncTokenManager, SyncTokenManager
from applifting_sdk.http import AsyncBaseClient, SyncBaseClient
from applifting_sdk.resources import AsyncOffersAPI, AsyncProductsAPI, SyncOffersAPI, SyncProductsAPI


class AsyncAppliftingSDKClient:
    def __init__(self, refresh_token: str):
        self._token_manager = AsyncTokenManager(refresh_token=refresh_token)
        self._client = AsyncBaseClient(token_manager=self._token_manager)

        self.offers = AsyncOffersAPI(client=self._client)
        self.products = AsyncProductsAPI(client=self._client)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()

    async def aclose(self):
        await self._client.aclose()


class SyncAppliftingSDKClient:
    def __init__(self, refresh_token: str):
        self._token_manager = SyncTokenManager(refresh_token=refresh_token)
        self._client = SyncBaseClient(token_manager=self._token_manager)

        self.offers = SyncOffersAPI(client=self._client)
        self.products = SyncProductsAPI(client=self._client)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._client.close()
