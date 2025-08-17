"""
Tests for product models.
"""

from uuid import uuid4

from applifting_sdk.models import RegisterProductRequest, RegisterProductResponse


class TestRegisterProductRequest:
    """Test RegisterProductRequest model."""

    def test_valid_product(self):
        """Test creating RegisterProductRequest with valid data."""
        product_id = uuid4()
        request = RegisterProductRequest(id=product_id, name="Test Product", description="A test product description")
        assert request.id == product_id
        assert request.name == "Test Product"
        assert request.description == "A test product description"

    def test_empty_description(self):
        """Test creating RegisterProductRequest with empty description."""
        request = RegisterProductRequest(id=uuid4(), name="Product Name", description="")
        assert request.description == ""

    def test_model_serialization(self):
        """Test model serialization to dict."""
        request = RegisterProductRequest(id=uuid4(), name="Serialization Test", description="Testing serialization")
        data = request.model_dump()
        assert data["name"] == "Serialization Test"
        assert data["description"] == "Testing serialization"
        assert "id" in data


class TestRegisterProductResponse:
    """Test RegisterProductResponse model."""

    def test_valid_response(self):
        """Test creating RegisterProductResponse with valid data."""
        product_id = uuid4()
        response = RegisterProductResponse(id=product_id)
        assert response.id == product_id

    def test_model_serialization(self):
        """Test model serialization to dict."""
        response = RegisterProductResponse(id=uuid4())
        data = response.model_dump()
        assert "id" in data
        assert len(data) == 1
