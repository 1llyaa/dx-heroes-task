"""
Tests for offer models.
"""

from uuid import uuid4

from applifting_sdk.models import OfferResponse


class TestOfferResponse:
    """Test OfferResponse model."""

    def test_valid_offer(self):
        """Test creating OfferResponse with valid data."""
        product_id = uuid4()
        offer = OfferResponse(id=uuid4(), price=1000, items_in_stock=50)
        assert offer.price == 1000
        assert offer.items_in_stock == 50

    def test_zero_values(self):
        """Test creating OfferResponse with zero values."""
        offer = OfferResponse(id=uuid4(), price=0, items_in_stock=0)
        assert offer.price == 0
        assert offer.items_in_stock == 0

    def test_model_serialization(self):
        """Test model serialization to dict."""
        offer = OfferResponse(id=uuid4(), price=2500, items_in_stock=25)
        data = offer.model_dump()
        assert data["price"] == 2500
        assert data["items_in_stock"] == 25
        assert "id" in data
