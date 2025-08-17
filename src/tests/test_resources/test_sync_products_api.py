"""
Tests for ProductsAPI.
"""

import pytest
from unittest.mock import Mock
from uuid import uuid4
from applifting_sdk.resources import SyncProductsAPI
from applifting_sdk.models import RegisterProductRequest, RegisterProductResponse


class TestSyncProductsAPI:
    """Test ProductsAPI."""

    def test_initialization(self):
        """Test ProductsAPI initialization."""
        mock_client = Mock()
        api = SyncProductsAPI(mock_client)
        assert api._client == mock_client

    @pytest.mark.asyncio
    async def test_register_product_success(self):
        """Test successful register_product call."""
        mock_client = Mock()
        mock_client._request = Mock()

        expected_id = uuid4()
        mock_response = Mock()
        mock_response.json.return_value = {"id": str(expected_id)}
        mock_client._request.return_value = mock_response

        api = SyncProductsAPI(mock_client)
        product = RegisterProductRequest(id=uuid4(), name="Test Product", description="A test product")

        result = api.register_product(product)

        assert isinstance(result, RegisterProductResponse)
        assert result.id == expected_id

    @pytest.mark.asyncio
    async def test_register_product_endpoint_construction(self):
        """Test that endpoint is constructed correctly."""
        mock_client = Mock()
        mock_client._request = Mock()

        mock_response = Mock()
        mock_response.json.return_value = {"id": str(uuid4())}
        mock_client._request.return_value = mock_response

        api = SyncProductsAPI(mock_client)
        product = RegisterProductRequest(id=uuid4(), name="Test Product", description="A test product")

        api.register_product(product)

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/api/v1/products/register" in call_args[1]["endpoint"]

    @pytest.mark.asyncio
    async def test_register_product_json_parameter(self):
        """Test that JSON parameter is properly serialized."""
        mock_client = Mock()
        mock_client._request = Mock()

        mock_response = Mock()
        mock_response.json.return_value = {"id": str(uuid4())}
        mock_client._request.return_value = mock_response

        api = SyncProductsAPI(mock_client)
        product = RegisterProductRequest(id=uuid4(), name="Test Product", description="A test product")

        api.register_product(product)

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        json_data = call_args[1]["json"]
        assert json_data["name"] == "Test Product"
        assert json_data["description"] == "A test product"
