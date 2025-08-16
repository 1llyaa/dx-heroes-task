"""
Tests for authentication models.
"""

import pytest
from applifting_sdk.models import AuthResponse


class TestAuthResponse:
    """Test AuthResponse model."""

    def test_valid_token(self):
        """Test creating AuthResponse with valid token."""
        response = AuthResponse(access_token="valid_token_123")
        assert response.access_token == "valid_token_123"

    def test_empty_token(self):
        """Test creating AuthResponse with empty token."""
        response = AuthResponse(access_token="")
        assert response.access_token == ""

    def test_model_serialization(self):
        """Test model serialization to dict."""
        response = AuthResponse(access_token="test_token")
        data = response.model_dump()
        assert data["access_token"] == "test_token"
        assert len(data) == 1
