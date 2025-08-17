"""
Common fixtures for the Applifting SDK test suite.
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import httpx
import pytest

from applifting_sdk.models import (
    AuthResponse,
    OfferResponse,
    RegisterProductRequest,
    RegisterProductResponse,
)
from applifting_sdk.models.validation import HTTPValidationError

# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_uuid() -> UUID:
    """Generate a sample UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_refresh_token() -> str:
    """Sample refresh token for testing."""
    return "test_refresh_token_12345"


@pytest.fixture
def sample_access_token() -> str:
    """Sample access token for testing."""
    return "test_access_token_67890"


@pytest.fixture
def sample_auth_response(sample_access_token) -> AuthResponse:
    """Sample authentication response."""
    return AuthResponse(access_token=sample_access_token)


@pytest.fixture
def sample_register_product_request(sample_uuid) -> RegisterProductRequest:
    """Sample product registration request."""
    return RegisterProductRequest(
        id=sample_uuid, name="Test Product", description="A test product for testing purposes"
    )


@pytest.fixture
def sample_register_product_response(sample_uuid) -> RegisterProductResponse:
    """Sample product registration response."""
    return RegisterProductResponse(id=sample_uuid)


@pytest.fixture
def sample_offer_response(sample_uuid) -> OfferResponse:
    """Sample offer response."""
    return OfferResponse(id=sample_uuid, price=1999, items_in_stock=42)  # 19.99 in cents


@pytest.fixture
def sample_offers_list(sample_uuid) -> list[OfferResponse]:
    """Sample list of offers."""
    return [
        OfferResponse(id=uuid4(), price=1999, items_in_stock=42),
        OfferResponse(id=uuid4(), price=2499, items_in_stock=15),
        OfferResponse(id=uuid4(), price=999, items_in_stock=100),
    ]


@pytest.fixture
def sample_validation_error() -> HTTPValidationError:
    """Sample validation error response."""
    return HTTPValidationError(
        detail=[{"loc": ["body", "name"], "msg": "field required", "type": "value_error.missing"}]
    )


# ============================================================================
# HTTP Response Fixtures
# ============================================================================


@pytest.fixture
def mock_success_response() -> httpx.Response:
    """Mock successful HTTP response."""
    return httpx.Response(
        status_code=200, json=lambda: {"message": "Success"}, headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_auth_success_response(sample_access_token) -> httpx.Response:
    """Mock successful authentication response."""
    return httpx.Response(
        status_code=200,
        json=lambda: {"access_token": sample_access_token},
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture
def mock_offers_response(sample_offers_list) -> httpx.Response:
    """Mock offers list response."""
    offers_data = [
        {"id": str(offer.id), "price": offer.price, "items_in_stock": offer.items_in_stock}
        for offer in sample_offers_list
    ]
    return httpx.Response(status_code=200, json=lambda: offers_data, headers={"Content-Type": "application/json"})


@pytest.fixture
def mock_product_register_response(sample_uuid) -> httpx.Response:
    """Mock product registration response."""
    return httpx.Response(
        status_code=200, json=lambda: {"id": str(sample_uuid)}, headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_401_response() -> httpx.Response:
    """Mock 401 Unauthorized response."""
    return httpx.Response(
        status_code=401, json=lambda: {"detail": "Unauthorized"}, headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_403_response() -> httpx.Response:
    """Mock 403 Forbidden response."""
    return httpx.Response(
        status_code=403, json=lambda: {"detail": "Forbidden"}, headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_404_response() -> httpx.Response:
    """Mock 404 Not Found response."""
    return httpx.Response(
        status_code=404, json=lambda: {"detail": "Not Found"}, headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_409_response() -> httpx.Response:
    """Mock 409 Conflict response."""
    return httpx.Response(
        status_code=409, json=lambda: {"detail": "Conflict"}, headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_422_response(sample_validation_error) -> httpx.Response:
    """Mock 422 Validation Failed response."""
    return httpx.Response(
        status_code=422, json=lambda: sample_validation_error.model_dump(), headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_429_response() -> httpx.Response:
    """Mock 429 Rate Limit response."""
    return httpx.Response(
        status_code=429, json=lambda: {"detail": "Too Many Requests"}, headers={"Content-Type": "application/json"}
    )


@pytest.fixture
def mock_500_response() -> httpx.Response:
    """Mock 500 Server Error response."""
    return httpx.Response(
        status_code=500, json=lambda: {"detail": "Internal Server Error"}, headers={"Content-Type": "application/json"}
    )


# ============================================================================
# Mock Object Fixtures
# ============================================================================


@pytest.fixture
def mock_token_manager() -> Mock:
    """Mock token manager for testing."""
    mock = Mock()
    mock.get_access_token = AsyncMock(return_value="mock_access_token")
    return mock


@pytest.fixture
def mock_httpx_client() -> Mock:
    """Mock httpx AsyncClient for testing."""
    mock = Mock()
    mock.request = AsyncMock()
    mock.aclose = AsyncMock()
    return mock


@pytest.fixture
def mock_async_client(mock_token_manager) -> Mock:
    """Mock AsyncBaseClient for testing."""
    mock = Mock()
    mock._token_manager = mock_token_manager
    mock._request = AsyncMock()
    mock.aclose = AsyncMock()
    return mock


# ============================================================================
# File System Fixtures
# ============================================================================


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def temp_cache_file(temp_cache_dir):
    """Create a temporary cache file for testing."""
    cache_file = temp_cache_dir / "token_cache.json"
    return cache_file


@pytest.fixture
def sample_cache_data(sample_access_token):
    """Sample cache data for testing."""
    return {"access_token": sample_access_token, "expires_at": 9999999999.0}  # Far future timestamp


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def test_settings():
    """Test configuration settings."""
    return {
        "base_url": "https://test.api.local",
        "token_expiration_seconds": 300,
        "token_expiration_buffer_seconds": 5,
        "refresh_token": "test_refresh_token",
    }


# ============================================================================
# Error Fixtures
# ============================================================================


@pytest.fixture
def network_error():
    """Simulate a network error."""
    return httpx.NetworkError("Network error occurred")


@pytest.fixture
def timeout_error():
    """Simulate a timeout error."""
    return httpx.ConnectTimeout("Connection timed out")


@pytest.fixture
def read_timeout_error():
    """Simulate a read timeout error."""
    return httpx.ReadTimeout("Read timed out")
