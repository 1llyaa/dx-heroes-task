"""
Tests for API exceptions.
"""

import pytest
from applifting_sdk.exceptions import (
    AppliftingSDKError,
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
    APIError,
    AuthenticationError,
    NotFoundError,
    ServerError,
    ValidationFailed,
)


class TestAppliftingSDKError:
    """Test base AppliftingSDKError."""

    def test_error_creation(self):
        """Test creating error with message."""
        error = AppliftingSDKError("Test error message")
        assert str(error) == "Test error message"

    def test_error_without_message(self):
        """Test creating error without message."""
        error = AppliftingSDKError()
        assert str(error) == ""


class TestAppliftingSDKNetworkError:
    """Test AppliftingSDKNetworkError."""

    def test_network_error_creation(self):
        """Test creating network error."""
        error = AppliftingSDKNetworkError("Network failed")
        assert str(error) == "Network failed"
        assert isinstance(error, AppliftingSDKError)


class TestAppliftingSDKTimeoutError:
    """Test AppliftingSDKTimeoutError."""

    def test_timeout_error_creation(self):
        """Test creating timeout error."""
        error = AppliftingSDKTimeoutError("Request timed out")
        assert str(error) == "Request timed out"
        assert isinstance(error, AppliftingSDKError)


class TestAPIError:
    """Test APIError and its subclasses."""

    def test_api_error_creation(self):
        """Test creating API error."""
        error = APIError(500, "Internal Server Error")
        assert str(error) == "500 Internal Server Error"

    def test_authentication_error(self):
        """Test authentication error."""
        error = AuthenticationError(401, "Unauthorized")
        assert str(error) == "401 Unauthorized"
        assert isinstance(error, APIError)

    def test_not_found_error(self):
        """Test not found error."""
        error = NotFoundError(404, "Not Found")
        assert str(error) == "404 Not Found"
        assert isinstance(error, APIError)

    def test_server_error(self):
        """Test server error."""
        error = ServerError(500, "Internal Server Error")
        assert str(error) == "500 Internal Server Error"
        assert isinstance(error, APIError)

    def test_validation_failed(self):
        """Test validation failed error."""
        error = ValidationFailed(422, "Validation Failed")
        assert str(error) == "422 Validation Failed"
        assert isinstance(error, APIError)
