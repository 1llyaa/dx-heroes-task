"""
Tests for AsyncBaseClient.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from applifting_sdk.http import AsyncBaseClient
from applifting_sdk.exceptions import (
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
    AuthenticationError,
    NotFoundError,
    ServerError,
    ValidationFailed,
)


class TestAsyncBaseClient:
    """Test AsyncBaseClient."""

    def test_initialization(self):
        """Test client initialization."""
        mock_token_manager = Mock()
        client = AsyncBaseClient(mock_token_manager)
        assert client._base_url == "https://api.test.local"
        assert client._token_manager == mock_token_manager

    @pytest.mark.asyncio
    async def test_request_with_headers(self):
        """Test request with custom headers."""
        mock_token_manager = Mock()
        mock_token_manager.get_access_token = AsyncMock(return_value="test_token")

        client = AsyncBaseClient(mock_token_manager)

        # Mock the httpx client to avoid real HTTP calls
        with patch("httpx.AsyncClient.request") as mock_httpx_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_httpx_request.return_value = mock_response

            # This will actually execute the real _request method
            await client._request("GET", "/test", headers={"Custom": "header"})

            # Verify the request was made with proper headers
            mock_httpx_request.assert_called_once()
            call_args = mock_httpx_request.call_args
            assert call_args[1]["headers"]["Bearer"] == "test_token"
            assert call_args[1]["headers"]["Custom"] == "header"

    @pytest.mark.asyncio
    async def test_request_with_params(self):
        """Test request with query parameters."""
        mock_token_manager = Mock()
        mock_token_manager.get_access_token = AsyncMock(return_value="test_token")

        client = AsyncBaseClient(mock_token_manager)

        with patch("httpx.AsyncClient.request") as mock_httpx_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_httpx_request.return_value = mock_response

            await client._request("GET", "/test", params={"page": 1, "limit": 10})

            mock_httpx_request.assert_called_once()
            call_args = mock_httpx_request.call_args
            assert call_args[1]["params"] == {"page": 1, "limit": 10}

    @pytest.mark.asyncio
    async def test_request_with_json(self):
        """Test request with JSON data."""
        mock_token_manager = Mock()
        mock_token_manager.get_access_token = AsyncMock(return_value="test_token")

        client = AsyncBaseClient(mock_token_manager)

        with patch("httpx.AsyncClient.request") as mock_httpx_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_httpx_request.return_value = mock_response

            json_data = {"name": "test", "value": 42}
            await client._request("POST", "/test", json=json_data)

            mock_httpx_request.assert_called_once()
            call_args = mock_httpx_request.call_args
            assert call_args[1]["json"] == json_data

    def test_uuid_serialization_helper(self):
        """Test that UUIDs are serialized by the _to_jsonable helper."""
        from applifting_sdk.helpers.uuid_serializer import _to_jsonable

        test_uuid = uuid4()
        json_data = {"id": test_uuid}

        result = _to_jsonable(json_data)
        assert result["id"] == str(test_uuid)
        assert isinstance(result["id"], str)
