from uuid import UUID

import httpx
import requests

from applifting_sdk.http import AsyncBaseClient, SyncBaseClient
from applifting_sdk.models import OfferResponse


class AsyncOffersAPI:
    """
    Async API client for /offers endpoints.
    """

    def __init__(self, client: AsyncBaseClient):
        self._client: AsyncBaseClient = client

    async def get_offers(self, product_id: UUID) -> list[OfferResponse]:
        """
        Get all offers for a given product ID.
        """
        endpoint: str = f"/api/v1/products/{product_id}/offers"
        response: httpx.Response = await self._client._request(method="GET", endpoint=endpoint)
        offers_data: dict = response.json()
        # TODO - Check this response
        return [OfferResponse(**offer) for offer in offers_data]


class SyncOffersAPI:
    """
    Sync API client for /offers endpoints.
    """

    def __init__(self, client: SyncBaseClient):
        self._client: SyncBaseClient = client

    def get_offers(self, product_id: UUID) -> list[OfferResponse]:
        """
        Get all offers for a given product ID.
        """
        endpoint: str = f"/api/v1/products/{product_id}/offers"
        response: requests.Response = self._client._request(method="GET", endpoint=endpoint)
        offers_data: dict = response.json()

        return [OfferResponse(**offer) for offer in offers_data]
