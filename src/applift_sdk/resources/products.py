from applift_sdk.http import AsyncBaseClient
from applift_sdk.models import RegisterProductRequest, RegisterProductResponse


class ProductsAPI:
    """
    API client for /products endpoints.
    """

    def __init__(self, client: AsyncBaseClient):
        self._client = client

    async def register_product(self, product: RegisterProductRequest) -> RegisterProductResponse:
        """
        Register a new product.
        """
        endpoint = "/api/v1/products/register"
        response = await self._client._request(method="POST", endpoint=endpoint, json=product.dict())
        return RegisterProductResponse(**response.json())
