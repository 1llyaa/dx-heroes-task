import httpx
import requests

from applifting_sdk.http import AsyncBaseClient, SyncBaseClient
from applifting_sdk.models import RegisterProductRequest, RegisterProductResponse


class AsyncProductsAPI:
    """
    Sync API client for /products endpoints.
    """

    def __init__(self, client: AsyncBaseClient):
        self._client: AsyncBaseClient = client

    async def register_product(self, product: RegisterProductRequest) -> RegisterProductResponse:
        """
        Register a new product.
        """

        endpoint: str = "/api/v1/products/register"
        response: httpx.Response = await self._client._request(
            method="POST", endpoint=endpoint, json=product.model_dump()
        )
        return RegisterProductResponse(**response.json())

class SyncProductsAPI:
    """
    Sync API client for /products endpoints.
    """

    def __init__(self, client: SyncBaseClient):
        self._client: SyncBaseClient = client

    def register_product(self, product: RegisterProductRequest) -> RegisterProductResponse:
        """
        Register a new product.
        """

        endpoint: str = "/api/v1/products/register"
        response: requests.Response = self._client._request(
            method="POST", endpoint=endpoint, json=product.model_dump()
        )
        return RegisterProductResponse(**response.json())