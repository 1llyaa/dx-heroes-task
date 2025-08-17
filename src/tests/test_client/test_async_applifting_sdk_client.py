"""
Tests for AsyncAppliftingSDKClient.
"""

import pytest
from unittest.mock import patch
from applifting_sdk.client import AsyncAppliftingSDKClient


class TestAsyncAppliftingSDKClient:
    """Test AsyncAppliftingSDKClient."""

    def test_initialization(self):
        """Test client initialization."""
        client = AsyncAppliftingSDKClient("test_token")
        assert client._token_manager is not None

    def test_empty_refresh_token(self):
        """Test initialization with empty refresh token."""
        client = AsyncAppliftingSDKClient("")
        assert client._token_manager is not None

    def test_none_refresh_token(self):
        """Test initialization with None refresh token."""
        client = AsyncAppliftingSDKClient(None)
        assert client._token_manager is not None

    def test_component_creation(self):
        """Test that components are created."""
        client = AsyncAppliftingSDKClient("test_token")

        # Check that components exist
        assert client._token_manager is not None
        assert client._client is not None
        assert client.offers is not None
        assert client.products is not None

    @pytest.mark.asyncio
    async def test_aclose(self):
        """Test client cleanup."""
        client = AsyncAppliftingSDKClient("test_token")

        with patch.object(client._client, "aclose") as mock_close:
            await client.aclose()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test context manager behavior."""
        client = AsyncAppliftingSDKClient("test_token")

        with patch.object(client._client, "aclose") as mock_close:
            async with client:
                pass
            mock_close.assert_called_once()

    def test_api_access(self):
        """Test that API clients are accessible."""
        client = AsyncAppliftingSDKClient("test_token")

        assert client.offers is not None
        assert client.products is not None
