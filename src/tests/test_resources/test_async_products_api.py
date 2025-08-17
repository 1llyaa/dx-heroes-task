"""
Tests for ProductsAPI.
"""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from applifting_sdk.models import RegisterProductRequest, RegisterProductResponse
from applifting_sdk.resources import AsyncProductsAPI


class TestAsyncProductsAPI:
    """Test ProductsAPI."""

    def test_initialization(self):
        """Test ProductsAPI initialization."""
        mock_client = Mock()
        api = AsyncProductsAPI(mock_client)
        assert api._client == mock_client

    @pytest.mark.asyncio
    async def test_register_product_success(self):
        """Test successful register_product call."""
        mock_client = Mock()
        mock_client._request = AsyncMock()

        expected_id = uuid4()
        mock_response = Mock()
        mock_response.json.return_value = {"id": str(expected_id)}
        mock_client._request.return_value = mock_response

        api = AsyncProductsAPI(mock_client)
        product = RegisterProductRequest(id=uuid4(), name="Test Product", description="A test product")

        result = await api.register_product(product)

        assert isinstance(result, RegisterProductResponse)
        assert result.id == expected_id

    @pytest.mark.asyncio
    async def test_register_product_endpoint_construction(self):
        """Test that endpoint is constructed correctly."""
        mock_client = Mock()
        mock_client._request = AsyncMock()

        mock_response = Mock()
        mock_response.json.return_value = {"id": str(uuid4())}
        mock_client._request.return_value = mock_response

        api = AsyncProductsAPI(mock_client)
        product = RegisterProductRequest(id=uuid4(), name="Test Product", description="A test product")

        await api.register_product(product)

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/api/v1/products/register" in call_args[1]["endpoint"]

    @pytest.mark.asyncio
    async def test_register_product_json_parameter(self):
        """Test that JSON parameter is properly serialized."""
        mock_client = Mock()
        mock_client._request = AsyncMock()

        mock_response = Mock()
        mock_response.json.return_value = {"id": str(uuid4())}
        mock_client._request.return_value = mock_response

        api = AsyncProductsAPI(mock_client)
        product = RegisterProductRequest(id=uuid4(), name="Test Product", description="A test product")

        await api.register_product(product)

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        json_data = call_args[1]["json"]
        assert json_data["name"] == "Test Product"
        assert json_data["description"] == "A test product"
