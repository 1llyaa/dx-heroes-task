import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
import requests


from applifting_sdk.http import SyncBaseClient
from applifting_sdk.exceptions import (
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
    AuthenticationError,
    NotFoundError,
    ServerError,
    ValidationFailed,
)


class TestSyncBaseClient:
    """Test SyncBaseClient."""

    def setup_method(self):
        """Setup for each test method."""
        self.mock_token_manager = Mock()
        self.mock_token_manager.get_access_token = Mock(return_value="test_token")

        self.refresh_token = "test_refresh_token"
        self.cache_dir = "/tmp/test_cache"
        self.base_url = "https://api.test.local"

        self.default_settings = {
            "token_expiration_seconds": 300,
            "token_expiration_buffer_seconds": 5,
            "base_url": self.base_url,
        }

    def _create_mock_settings(self, **overrides):
        """Helper to create mock settings with defaults and overrides."""
        settings = self.default_settings.copy()
        settings.update(overrides)
        return settings

    def _create_mock_response(
        self,
        status_code: int = 200,
        json_data: dict = None,
        ok: bool = True,
        json_exception: Exception = None,
    ):
        """Helper to create mock requests.Response objects."""
        mock_response = Mock(spec=requests.Response)
        mock_response.status_code = status_code
        mock_response.ok = ok

        if json_exception:
            mock_response.json.side_effect = json_exception
        else:
            mock_response.json.return_value = json_data or {"access_token": "test_token"}

        return mock_response

    def test_initialization(self):
        """Test client initialization."""
        with patch("applifting_sdk.config.settings") as mock_settings:
            mock_settings.base_url = "https://api.test.local"

            client = SyncBaseClient(self.mock_token_manager)
            assert client._base_url == "https://api.test.local"
            assert client._token_manager == self.mock_token_manager
            assert client._session is not None
            assert client.error_handler is not None

    def test_request_success_basic(self):
        """Test successful basic request."""
        client = SyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.return_value = mock_response
            mock_request.ok = True

            result = client._request("GET", "/test")

            # Verify token manager was called
            self.mock_token_manager.get_access_token.assert_called_once()

            # Verify requests request was called with correct args
            mock_request.assert_called_once_with(
                method="GET",
                url="https://api.test.local/test",
                headers={"Bearer": "test_token"},
                params=None,
                json=None,
            )

            assert result == mock_response

    def test_request_with_headers(self):
        """Test request with custom headers."""
        client = SyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.return_value = mock_response

            client._request("GET", "/test", headers={"Custom": "header", "Another": "value"})

            # Verify headers are merged correctly
            expected_headers = {"Bearer": "test_token", "Custom": "header", "Another": "value"}

            call_args = mock_request.call_args
            assert call_args[1]["headers"] == expected_headers

    def test_request_with_params(self):
        """Test request with query parameters."""
        client = SyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.return_value = mock_response

            params = {"page": 1, "limit": 10, "search": "test"}
            client._request("GET", "/test", params=params)

            call_args = mock_request.call_args
            assert call_args[1]["params"] == params

    def test_request_with_json(self):
        """Test request with JSON data."""
        client = SyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.return_value = mock_response

            json_data = {"name": "test", "value": 42, "active": True}
            client._request("POST", "/test", json=json_data)

            call_args = mock_request.call_args
            assert call_args[1]["json"] == json_data

    def test_request_with_uuid_serialization(self):
        """Test request with UUID serialization in JSON data."""
        client = SyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.return_value = mock_response

            test_uuid = uuid4()
            json_data = {"id": test_uuid, "name": "test"}
            client._request("POST", "/test", json=json_data)

            # Verify UUID was serialized to string
            call_args = mock_request.call_args
            assert call_args[1]["json"]["id"] == str(test_uuid)
            assert call_args[1]["json"]["name"] == "test"

    def test_request_all_parameters(self):
        """Test request with all parameters."""
        client = SyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(201)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.return_value = mock_response

            test_uuid = uuid4()
            headers = {"Content-Type": "application/json", "X-Custom": "value"}
            params = {"version": "v1"}
            json_data = {"id": test_uuid, "data": {"nested": "value"}}

            client._request("PUT", "/test/endpoint", headers=headers, params=params, json=json_data)

            call_args = mock_request.call_args
            expected_headers = {"Bearer": "test_token", "Content-Type": "application/json", "X-Custom": "value"}

            assert call_args[1]["method"] == "PUT"
            assert call_args[1]["url"] == f"https://api.test.local/test/endpoint"
            assert call_args[1]["headers"] == expected_headers
            assert call_args[1]["params"] == params
            assert call_args[1]["json"]["id"] == str(test_uuid)
            assert call_args[1]["json"]["data"]["nested"] == "value"

    def test_request_connect_timeout_error(self):
        """Test ConnectTimeout exception handling."""
        client = SyncBaseClient(self.mock_token_manager)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.side_effect = requests.ConnectTimeout("Connection timed out")

            with pytest.raises(AppliftingSDKTimeoutError) as exc_info:
                client._request("GET", "/test")

            assert "Connection timed out" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == requests.ConnectTimeout

    def test_request_read_timeout_error(self):
        """Test ReadTimeout exception handling."""
        client = SyncBaseClient(self.mock_token_manager)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.side_effect = requests.ReadTimeout("Read timed out")

            with pytest.raises(AppliftingSDKTimeoutError) as exc_info:
                client._request("GET", "/test")

            assert "Read timed out" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == requests.ReadTimeout

    def test_request_network_error(self):
        """Test NetworkError exception handling."""
        client = SyncBaseClient(self.mock_token_manager)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.side_effect = requests.ConnectionError("Network error")

            with pytest.raises(AppliftingSDKNetworkError) as exc_info:
                client._request("GET", "/test")

            assert "Network error" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == requests.ConnectionError

    def test_request_connect_error(self):
        """Test ConnectError exception handling."""
        client = SyncBaseClient(self.mock_token_manager)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.side_effect = requests.ConnectionError("Connection error")

            with pytest.raises(AppliftingSDKNetworkError) as exc_info:
                client._request("GET", "/test")

            assert "Connection error" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == requests.ConnectionError

    def test_request_remote_protocol_error(self):
        """Test RemoteProtocolError exception handling."""
        client = SyncBaseClient(self.mock_token_manager)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.side_effect = requests.RequestException("Protocol error")

            with pytest.raises(AppliftingSDKNetworkError) as exc_info:
                client._request("GET", "/test")

            assert "Protocol error" in str(exc_info.value)
            assert exc_info.value.__cause__.__class__ == requests.RequestException

    def test_request_api_error_handling(self):
        """Test API error handling for non-success responses."""
        client = SyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(404, ok=False)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.return_value = mock_response

            with patch.object(client.error_handler, "raise_api_error") as mock_error_handler:
                mock_error_handler.side_effect = NotFoundError(404, "Not Found")

                with pytest.raises(NotFoundError):
                    client._request("GET", "/test")

                mock_error_handler.assert_called_once_with(mock_response)

    def test_request_different_http_methods(self):
        """Test different HTTP methods."""
        client = SyncBaseClient(self.mock_token_manager)
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

        for method in methods:
            mock_response = self._create_mock_response(200)

            with patch.object(client._session, "request", new_callable=Mock) as mock_request:
                mock_request.return_value = mock_response

                client._request(method, "/test")

                call_args = mock_request.call_args
                assert call_args[1]["method"] == method

    def test_close(self):
        """Test context manager close."""
        client = SyncBaseClient(self.mock_token_manager)

        with patch.object(client._session, "close", new_callable=Mock) as mock_close:
            client.close()
            mock_close.assert_called_once()

    def test__context_manager(self):
        """Test context manager usage."""
        mock_token_manager = Mock()

        with patch.object(SyncBaseClient, "__init__", return_value=None):
            client = SyncBaseClient.__new__(SyncBaseClient)
            client._session = Mock()
            client._session.close = Mock()

            with client as ctx_session:
                assert ctx_session == client

            client._session.close.assert_called_once()

    def test_context_manager_exception_handling(self):
        """Test context manager properly closes on exception."""
        mock_token_manager = Mock()

        with patch.object(SyncBaseClient, "__init__", return_value=None):
            client = SyncBaseClient.__new__(SyncBaseClient)
            client._session = Mock()
            client._session.close = Mock()

            try:
                with client:
                    raise ValueError("Test exception")
            except ValueError:
                pass

            client._session.close.assert_called_once()

    def test_uuid_serialization_helper_integration(self):
        """Test that UUIDs are properly serialized by the to_jsonable helper."""
        from applifting_sdk.helpers import JSONSerializer

        test_uuid = uuid4()
        complex_data = {
            "id": test_uuid,
            "user": {"uuid": test_uuid, "profile_id": uuid4()},
            "items": [{"item_id": uuid4(), "name": "item1"}, {"item_id": test_uuid, "name": "item2"}],
        }

        result = JSONSerializer.to_jsonable(complex_data)

        # Verify all UUIDs are converted to strings
        assert result["id"] == str(test_uuid)
        assert result["user"]["uuid"] == str(test_uuid)
        assert isinstance(result["user"]["profile_id"], str)
        assert isinstance(result["items"][0]["item_id"], str)
        assert result["items"][1]["item_id"] == str(test_uuid)

    def test_token_manager_integration(self):
        """Test proper integration with token manager."""
        # Test multiple calls to ensure token is fetched each time
        client = SyncBaseClient(self.mock_token_manager)
        mock_response = self._create_mock_response(200)

        with patch.object(client._session, "request", new_callable=Mock) as mock_request:
            mock_request.return_value = mock_response

            # Make multiple requests
            client._request("GET", "/test1")
            client._request("POST", "/test2")

            # Token should be fetched for each request
            assert self.mock_token_manager.get_access_token.call_count == 2

    def test_error_handler_integration(self):
        """Test proper integration with error handler."""
        client = SyncBaseClient(self.mock_token_manager)

        # Test different error status codes
        error_cases = [(401, AuthenticationError), (404, NotFoundError), (500, ServerError), (422, ValidationFailed)]

        for status_code, expected_exception in error_cases:
            mock_response = self._create_mock_response(status_code, ok=False)

            with patch.object(client._session, "request", new_callable=Mock) as mock_request:
                mock_request.return_value = mock_response

                with patch.object(client.error_handler, "raise_api_error") as mock_error_handler:
                    mock_error_handler.side_effect = expected_exception(status_code, "Test error")

                    with pytest.raises(expected_exception):
                        client._request("GET", "/test")

                    mock_error_handler.assert_called_once_with(mock_response)
