from applifting_sdk.auth import AsyncTokenManager
from applifting_sdk.http import AsyncBaseClient
from applifting_sdk.resources import AsyncOffersAPI, AsyncProductsAPI


class AppliftingSDKClient:
    def __init__(
        self,
        refresh_token: str,
    ):
        self._token_manager: AsyncTokenManager = AsyncTokenManager(refresh_token=refresh_token)
        self._client: AsyncBaseClient = AsyncBaseClient(token_manager=self._token_manager)

        self.offers: AsyncOffersAPI = AsyncOffersAPI(client=self._client)
        self.products: AsyncProductsAPI = AsyncProductsAPI(client=self._client)

    async def aclose(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()
