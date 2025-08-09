from applift_sdk.auth import AsyncTokenManager
from applift_sdk.http import AsyncBaseClient

from applift_sdk.resources import OffersAPI, ProductsAPI


class AppliftClient:
    def __init__(
        self,
        refresh_token: str,
        base_url: str = "https://python.exercise.applifting.cz",
    ):
        self._token_manager = AsyncTokenManager(
            refresh_token=refresh_token, base_url=base_url
        )
        self._client = AsyncBaseClient(
            base_url=base_url, token_manager=self._token_manager
        )

        self.offers = OffersAPI(client=self._client)
        self.products = ProductsAPI(client=self._client)

    async def aclose(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()
