import pytest
from unittest.mock import AsyncMock, Mock, patch, PropertyMock
from uuid import uuid4
import httpx
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

    def setup_method(self):
        """Setup for each test method."""
        self.mock_token_manager = Mock()
        self.mock_token_manager.get_access_token = AsyncMock(return_value="test_token")

    def _create_mock_response(self, status_code: int, is_success: bool = None):
        """Helper to create mock httpx.Response objects."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = status_code
        if is_success is None:
            is_success = 200 <= status_code < 300
        mock_response.is_success = is_success
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = Mock(return_value={"message": "test"})
        type(mock_response).text = PropertyMock(return_value="test response")
        return mock_response

    def test_initialization(self):
        """Test client initialization."""
        with patch("applifting_sdk.config.settings") as mock_settings:
            mock_settings.base_url = "https://api.test.local"

            client = AsyncBaseClient(self.mock_token_manager)
            assert client._base_url == "https://api.test.local"
            assert client._token_manager == self.mock_token_manager
            assert client._client is not None
            assert client.error_handler is not None

    @pytest.mark.asyncio
    async def test_request_success_basic(self):
        """Test successful basic request."""
        client = AsyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client._request("GET", "/test")

            # Verify token manager was called
            self.mock_token_manager.get_access_token.assert_called_once()

            # Verify httpx request was called with correct args
            mock_request.assert_called_once_with(
                method="GET",
                url="/test",
                headers={"Bearer": "test_token"},
                params=None,
                json=None,
            )

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_request_with_headers(self):
        """Test request with custom headers."""
        client = AsyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client._request("GET", "/test", headers={"Custom": "header", "Another": "value"})

            # Verify headers are merged correctly
            expected_headers = {
                "Bearer": "test_token",
                "Custom": "header",
                "Another": "value"
            }

            call_args = mock_request.call_args
            assert call_args[1]["headers"] == expected_headers

    @pytest.mark.asyncio
    async def test_request_with_params(self):
        """Test request with query parameters."""
        client = AsyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            params = {"page": 1, "limit": 10, "search": "test"}
            await client._request("GET", "/test", params=params)

            call_args = mock_request.call_args
            assert call_args[1]["params"] == params

    @pytest.mark.asyncio
    async def test_request_with_json(self):
        """Test request with JSON data."""
        client = AsyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            json_data = {"name": "test", "value": 42, "active": True}
            await client._request("POST", "/test", json=json_data)

            call_args = mock_request.call_args
            assert call_args[1]["json"] == json_data

    @pytest.mark.asyncio
    async def test_request_with_uuid_serialization(self):
        """Test request with UUID serialization in JSON data."""
        client = AsyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            test_uuid = uuid4()
            json_data = {"id": test_uuid, "name": "test"}
            await client._request("POST", "/test", json=json_data)

            # Verify UUID was serialized to string
            call_args = mock_request.call_args
            assert call_args[1]["json"]["id"] == str(test_uuid)
            assert call_args[1]["json"]["name"] == "test"

    @pytest.mark.asyncio
    async def test_request_all_parameters(self):
        """Test request with all parameters."""
        client = AsyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(201)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            test_uuid = uuid4()
            headers = {"Content-Type": "application/json", "X-Custom": "value"}
            params = {"version": "v1"}
            json_data = {"id": test_uuid, "data": {"nested": "value"}}

            await client._request(
                "PUT",
                "/test/endpoint",
                headers=headers,
                params=params,
                json=json_data
            )

            call_args = mock_request.call_args
            expected_headers = {
                "Bearer": "test_token",
                "Content-Type": "application/json",
                "X-Custom": "value"
            }

            assert call_args[1]["method"] == "PUT"
            assert call_args[1]["url"] == "/test/endpoint"
            assert call_args[1]["headers"] == expected_headers
            assert call_args[1]["params"] == params
            assert call_args[1]["json"]["id"] == str(test_uuid)
            assert call_args[1]["json"]["data"]["nested"] == "value"

    @pytest.mark.asyncio
    async def test_request_connect_timeout_error(self):
        """Test ConnectTimeout exception handling."""
        client = AsyncBaseClient(self.mock_token_manager)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.ConnectTimeout("Connection timed out")

            with pytest.raises(AppliftingSDKTimeoutError) as exc_info:
                await client._request("GET", "/test")

            assert "Connection timed out" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == httpx.ConnectTimeout

    @pytest.mark.asyncio
    async def test_request_read_timeout_error(self):
        """Test ReadTimeout exception handling."""
        client = AsyncBaseClient(self.mock_token_manager)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.ReadTimeout("Read timed out")

            with pytest.raises(AppliftingSDKTimeoutError) as exc_info:
                await client._request("GET", "/test")

            assert "Read timed out" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == httpx.ReadTimeout

    @pytest.mark.asyncio
    async def test_request_network_error(self):
        """Test NetworkError exception handling."""
        client = AsyncBaseClient(self.mock_token_manager)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.NetworkError("Network error")

            with pytest.raises(AppliftingSDKNetworkError) as exc_info:
                await client._request("GET", "/test")

            assert "Network error" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == httpx.NetworkError

    @pytest.mark.asyncio
    async def test_request_connect_error(self):
        """Test ConnectError exception handling."""
        client = AsyncBaseClient(self.mock_token_manager)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.ConnectError("Connection error")

            with pytest.raises(AppliftingSDKNetworkError) as exc_info:
                await client._request("GET", "/test")

            assert "Connection error" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == httpx.ConnectError

    @pytest.mark.asyncio
    async def test_request_remote_protocol_error(self):
        """Test RemoteProtocolError exception handling."""
        client = AsyncBaseClient(self.mock_token_manager)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = httpx.RemoteProtocolError("Protocol error")

            with pytest.raises(AppliftingSDKNetworkError) as exc_info:
                await client._request("GET", "/test")

            assert "Protocol error" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == httpx.RemoteProtocolError

    @pytest.mark.asyncio
    async def test_request_api_error_handling(self):
        """Test API error handling for non-success responses."""
        client = AsyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(404, is_success=False)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            with patch.object(client.error_handler, "raise_api_error") as mock_error_handler:
                mock_error_handler.side_effect = NotFoundError(404, "Not Found")

                with pytest.raises(NotFoundError):
                    await client._request("GET", "/test")

                mock_error_handler.assert_called_once_with(mock_response)

    @pytest.mark.asyncio
    async def test_request_different_http_methods(self):
        """Test different HTTP methods."""
        client = AsyncBaseClient(self.mock_token_manager)
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            mock_response = self._create_mock_response(200)

            with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                await client._request(method, "/test")

                call_args = mock_request.call_args
                assert call_args[1]["method"] == method

    @pytest.mark.asyncio
    async def test_aclose(self):
        """Test async context manager close."""
        client = AsyncBaseClient(self.mock_token_manager)

        with patch.object(client._client, "aclose", new_callable=AsyncMock) as mock_aclose:
            await client.aclose()
            mock_aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager usage."""
        mock_token_manager = Mock()

        with patch.object(AsyncBaseClient, "__init__", return_value=None):
            client = AsyncBaseClient.__new__(AsyncBaseClient)
            client._client = Mock()
            client._client.aclose = AsyncMock()

            async with client as ctx_client:
                assert ctx_client == client

            client._client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_exception_handling(self):
        """Test context manager properly closes on exception."""
        mock_token_manager = Mock()

        with patch.object(AsyncBaseClient, "__init__", return_value=None):
            client = AsyncBaseClient.__new__(AsyncBaseClient)
            client._client = Mock()
            client._client.aclose = AsyncMock()

            try:
                async with client:
                    raise ValueError("Test exception")
            except ValueError:
                pass

            client._client.aclose.assert_called_once()

    def test_uuid_serialization_helper_integration(self):
        """Test that UUIDs are properly serialized by the _to_jsonable helper."""
        from applifting_sdk.helpers.uuid_serializer import _to_jsonable

        test_uuid = uuid4()
        complex_data = {
            "id": test_uuid,
            "user": {
                "uuid": test_uuid,
                "profile_id": uuid4()
            },
            "items": [
                {"item_id": uuid4(), "name": "item1"},
                {"item_id": test_uuid, "name": "item2"}
            ]
        }

        result = _to_jsonable(complex_data)

        # Verify all UUIDs are converted to strings
        assert result["id"] == str(test_uuid)
        assert result["user"]["uuid"] == str(test_uuid)
        assert isinstance(result["user"]["profile_id"], str)
        assert isinstance(result["items"][0]["item_id"], str)
        assert result["items"][1]["item_id"] == str(test_uuid)

    @pytest.mark.asyncio
    async def test_token_manager_integration(self):
        """Test proper integration with token manager."""
        # Test multiple calls to ensure token is fetched each time
        client = AsyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            # Make multiple requests
            await client._request("GET", "/test1")
            await client._request("POST", "/test2")

            # Token should be fetched for each request
            assert self.mock_token_manager.get_access_token.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handler_integration(self):
        """Test proper integration with error handler."""
        client = AsyncBaseClient(self.mock_token_manager)

        # Test different error status codes
        error_cases = [
            (401, AuthenticationError),
            (404, NotFoundError),
            (500, ServerError),
            (422, ValidationFailed)
        ]

        for status_code, expected_exception in error_cases:
            mock_response = self._create_mock_response(status_code, is_success=False)

            with patch.object(client._client, "request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                with patch.object(client.error_handler, "raise_api_error") as mock_error_handler:
                    mock_error_handler.side_effect = expected_exception(status_code, "Test error")

                    with pytest.raises(expected_exception):
                        await client._request("GET", "/test")

                    mock_error_handler.assert_called_once_with(mock_response)