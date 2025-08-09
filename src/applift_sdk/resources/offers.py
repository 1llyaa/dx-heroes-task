from uuid import UUID
from typing import List

from applift_sdk.http import AsyncBaseClient
from applift_sdk.models import OfferResponse


class OffersAPI:
    """
    API client for /offers endpoints.
    """

    def __init__(self, client: AsyncBaseClient):
        self._client = client

    async def get_offers(self, product_id: UUID) -> List[OfferResponse]:
        """
        Get all offers for a given product ID.
        """
        endpoint = f"/api/v1/products/{product_id}/offers"
        response = await self._client._request(
            method="GET",
            endpoint=endpoint
        )
        offers_data = response.json()
        #TODO - Check this response
        return [OfferResponse(**offer) for offer in offers_data]
