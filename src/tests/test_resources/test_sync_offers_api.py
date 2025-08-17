"""
Tests for OffersAPI.
"""

from unittest.mock import Mock
from uuid import uuid4

from applifting_sdk.models import OfferResponse
from applifting_sdk.resources import SyncOffersAPI


class TestSyncOffersAPI:
    """Test OffersAPI."""

    def test_initialization(self):
        """Test OffersAPI initialization."""
        mock_client = Mock()
        api = SyncOffersAPI(mock_client)
        assert api._client == mock_client

    async def test_get_offers_success(self):
        """Test successful get_offers call."""
        mock_client = Mock()
        mock_client._request = Mock()

        mock_response = Mock()
        mock_response.json.return_value = [{"id": str(uuid4()), "price": 1000, "items_in_stock": 10}]
        mock_client._request.return_value = mock_response

        api = SyncOffersAPI(mock_client)
        offers = api.get_offers(uuid4())

        assert len(offers) == 1
        assert isinstance(offers[0], OfferResponse)
        assert offers[0].price == 1000
        assert offers[0].items_in_stock == 10

    async def test_get_offers_empty_response(self):
        """Test get_offers with empty response."""
        mock_client = Mock()
        mock_client._request = Mock()

        mock_response = Mock()
        mock_response.json.return_value = []
        mock_client._request.return_value = mock_response

        api = SyncOffersAPI(mock_client)
        offers = api.get_offers(uuid4())

        assert offers == []

    async def test_get_offers_endpoint_construction(self):
        """Test that endpoint is constructed correctly."""
        mock_client = Mock()
        mock_client._request = Mock()

        mock_response = Mock()
        mock_response.json.return_value = []
        mock_client._request.return_value = mock_response

        product_id = uuid4()
        api = SyncOffersAPI(mock_client)
        api.get_offers(product_id)

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[1]["method"] == "GET"
        assert f"/api/v1/products/{product_id}/offers" in call_args[1]["endpoint"]
