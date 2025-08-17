"""
Tests for AsyncTokenManager.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from applifting_sdk.auth import AsyncTokenManager
from applifting_sdk.exceptions import (
    AppliftingSDKError,
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
    BadRequestError,
)


class TestAsyncTokenManager:
    """Test cases for AsyncTokenManager class."""

    def setup_method(self):
        """Setup fresh test environment for each test."""
        self.refresh_token = "test_refresh_token"
        self.cache_dir = "/tmp/test_cache"
        self.base_url = "https://api.test.local"

        # Common settings that most tests will use
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
        is_success: bool = True,
        json_exception: Exception = None,
    ):
        """Helper to create mock httpx.Response objects."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.is_success = is_success

        if json_exception:
            mock_response.json.side_effect = json_exception
        else:
            mock_response.json.return_value = json_data or {"access_token": "test_token"}

        return mock_response

    def _create_mock_client(self, response=None):
        """Helper to create mock httpx.AsyncClient with proper context manager setup."""
        mock_client = Mock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()

        if response:
            mock_client.post = AsyncMock(return_value=response)

        return mock_client

    def _create_mock_cache_file(self, content: str):
        """Helper to create mock file object for cache operations."""
        mock_file = Mock()
        mock_file.read.return_value = content
        return mock_file

    def _patch_common_dependencies(self, settings_overrides=None, cache_dir=None):
        """Helper to patch common dependencies with sensible defaults."""
        settings = self._create_mock_settings(**(settings_overrides or {}))

        # Return context manager for easy use in tests
        class CommonPatches:
            def __init__(self, settings, cache_dir):
                self.settings = settings
                self.cache_dir = cache_dir or "/tmp/test_cache"
                self.patches = []

            def __enter__(self):
                settings_patch = patch("applifting_sdk.auth.async_token_manager.settings")
                cache_patch = patch("applifting_sdk.auth.async_token_manager.user_cache_dir")

                mock_settings = settings_patch.__enter__()
                mock_cache_dir = cache_patch.__enter__()

                # Configure mocks
                for key, value in self.settings.items():
                    setattr(mock_settings, key, value)
                mock_cache_dir.return_value = self.cache_dir

                self.patches.extend([settings_patch, cache_patch])
                return mock_settings, mock_cache_dir

            def __exit__(self, *args):
                for patch_obj in reversed(self.patches):
                    patch_obj.__exit__(*args)

        return CommonPatches(settings, cache_dir)


class TestAsyncTokenManagerInitialization(TestAsyncTokenManager):
    """Test AsyncTokenManager initialization."""

    def test_empty_refresh_token(self):
        """Test initialization with empty refresh token."""
        with self._patch_common_dependencies():
            manager = AsyncTokenManager("")
            assert manager._refresh_token == ""

    def test_none_refresh_token(self):
        """Test initialization with None refresh token."""
        with self._patch_common_dependencies():
            manager = AsyncTokenManager(None)
            assert manager._refresh_token is None


class TestAsyncTokenManagerCaching(TestAsyncTokenManager):
    """Test AsyncTokenManager caching functionality."""

    @pytest.mark.asyncio
    @patch("builtins.open")
    @patch("applifting_sdk.auth.async_token_manager.os.path.exists")
    async def test_get_access_token_cached(self, mock_exists, mock_open):
        """Test getting cached access token."""
        with self._patch_common_dependencies() as (mock_settings, mock_cache_dir):
            mock_exists.return_value = True

            # Setup cache file mock
            cache_content = '{"access_token": "cached_token", "expires_at": 9999999999}'
            mock_file = self._create_mock_cache_file(cache_content)
            mock_open.return_value.__enter__.return_value = mock_file
            mock_open.return_value.__exit__.return_value = None

            manager = AsyncTokenManager(self.refresh_token)
            token = await manager.get_access_token()

            assert token == "cached_token"

    @pytest.mark.asyncio
    @patch("builtins.open")
    @patch("applifting_sdk.auth.async_token_manager.os.path.exists")
    async def test_cache_file_invalid_json(self, mock_exists, mock_open):
        """Test handling invalid JSON in cache file."""
        with self._patch_common_dependencies():
            mock_exists.return_value = True

            # Setup invalid JSON cache file
            mock_file = self._create_mock_cache_file("invalid json")
            mock_open.return_value.__enter__.return_value = mock_file
            mock_open.return_value.__exit__.return_value = None

            manager = AsyncTokenManager(self.refresh_token)

            # Should fall back to refreshing token
            with patch("httpx.AsyncClient") as mock_client_class:
                response = self._create_mock_response(json_data={"access_token": "new_token"})
                mock_client = self._create_mock_client(response)
                mock_client_class.return_value = mock_client

                token = await manager.get_access_token()
                assert token == "new_token"

    @pytest.mark.asyncio
    async def test_cache_file_missing_fields(self):
        """Test cache file with missing fields."""
        with self._patch_common_dependencies():
            manager = AsyncTokenManager(self.refresh_token)

            # Mock the _read_token_cache method to return None (missing fields)
            with patch.object(manager, "_read_token_cache", return_value=None):
                with patch("httpx.AsyncClient") as mock_client_class:
                    response = self._create_mock_response(json_data={"access_token": "new_token"})
                    mock_client = self._create_mock_client(response)
                    mock_client_class.return_value = mock_client

                    token = await manager.get_access_token()
                    assert token == "new_token"

    @pytest.mark.asyncio
    async def test_write_token_cache_success(self):
        """Test successful token cache writing."""
        with self._patch_common_dependencies():
            manager = AsyncTokenManager(self.refresh_token)
            manager._access_token = "test_token"
            manager._token_expires_at = 9999999999

            # Mock the file operations
            with patch("builtins.open") as mock_open:
                mock_file = Mock()
                mock_file.write = Mock()
                mock_open.return_value.__enter__.return_value = mock_file
                mock_open.return_value.__exit__.return_value = None

                # Should not raise any exception
                manager._write_token_cache("test_token")

                mock_open.assert_called_once()
                # The write method is called multiple times for JSON formatting, so check it was called
                assert mock_file.write.call_count > 0


class TestAsyncTokenManagerTokenRefresh(TestAsyncTokenManager):
    """Test AsyncTokenManager token refresh functionality."""

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.async_token_manager.os.path.exists")
    async def test_get_access_token_refresh(self, mock_exists):
        """Test refreshing access token."""
        with self._patch_common_dependencies():
            mock_exists.return_value = False  # No cache file

            manager = AsyncTokenManager(self.refresh_token)

            # Mock the HTTP request
            with patch("httpx.AsyncClient") as mock_client_class:
                response = self._create_mock_response(json_data={"access_token": "new_token"})
                mock_client = self._create_mock_client(response)
                mock_client_class.return_value = mock_client

                token = await manager.get_access_token()
                assert token == "new_token"

    @pytest.mark.asyncio
    async def test_refresh_token_request_success(self):
        """Test successful token refresh request."""
        with self._patch_common_dependencies():
            manager = AsyncTokenManager(self.refresh_token)

            with patch("httpx.AsyncClient") as mock_client_class:
                response = self._create_mock_response(json_data={"access_token": "new_token"})
                mock_client = self._create_mock_client(response)
                mock_client_class.return_value = mock_client

                await manager._refresh_token_request()
                assert manager._access_token == "new_token"

    @pytest.mark.asyncio
    async def test_refresh_token_request_no_refresh_token(self):
        """Test refresh request with no refresh token."""
        manager = AsyncTokenManager(None)

        with pytest.raises(AppliftingSDKError) as exc_info:
            await manager._refresh_token_request()

        assert "No refresh token was provided" in str(exc_info.value)
        assert manager._access_token is None


class TestAsyncTokenManagerNetworkErrors(TestAsyncTokenManager):
    """Test AsyncTokenManager network error handling."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception_class,expected_error,error_message",
        [
            (httpx.ConnectTimeout("Connection timed out"), AppliftingSDKTimeoutError, "Connection timed out"),
            (httpx.ReadTimeout("Read timed out"), AppliftingSDKTimeoutError, "Read timed out"),
            (httpx.NetworkError("Network error"), AppliftingSDKNetworkError, "Network error"),
        ],
    )
    @patch("httpx.AsyncClient.post")
    async def test_refresh_token_request_network_errors(
        self, mock_post, exception_class, expected_error, error_message
    ):
        """Test various network errors during token refresh."""
        manager = AsyncTokenManager(self.refresh_token)
        mock_post.side_effect = exception_class

        with pytest.raises(expected_error) as exc_info:
            await manager._refresh_token_request()

        assert error_message in str(exc_info.value)
        assert manager._access_token is None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_refresh_token_request_timeout_error(self, mock_post):
        """Test connection timeout error during token refresh."""
        manager = AsyncTokenManager(self.refresh_token)
        mock_post.side_effect = httpx.ConnectTimeout("Connection timed out")

        with pytest.raises(AppliftingSDKTimeoutError) as exc_info:
            await manager._refresh_token_request()

        assert "Connection timed out" in str(exc_info.value)
        assert manager._access_token is None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_refresh_token_request_read_timeout(self, mock_post):
        """Test read timeout error during token refresh."""
        manager = AsyncTokenManager(self.refresh_token)
        mock_post.side_effect = httpx.ReadTimeout("Read timed out")

        with pytest.raises(AppliftingSDKTimeoutError) as exc_info:
            await manager._refresh_token_request()

        assert "Read timed out" in str(exc_info.value)
        assert manager._access_token is None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_refresh_token_request_network_error(self, mock_post):
        """Test network error during token refresh."""
        manager = AsyncTokenManager(self.refresh_token)
        mock_post.side_effect = httpx.NetworkError("Network error")

        with pytest.raises(AppliftingSDKNetworkError) as exc_info:
            await manager._refresh_token_request()

        assert manager._access_token is None


class TestAsyncTokenManagerTokenExpiration(TestAsyncTokenManager):
    """Test AsyncTokenManager token expiration handling."""

    @pytest.mark.asyncio
    async def test_token_expired_with_buffer(self):
        """Test token expiration with buffer time."""
        with self._patch_common_dependencies():
            manager = AsyncTokenManager(self.refresh_token)
            manager._access_token = "old_token"
            manager._token_expires_at = 0  # Expired

            # Mock the HTTP request
            with patch("httpx.AsyncClient") as mock_client_class:
                response = self._create_mock_response(json_data={"access_token": "new_token"})
                mock_client = self._create_mock_client(response)
                mock_client_class.return_value = mock_client

                token = await manager.get_access_token()
                assert token == "new_token"

    @pytest.mark.asyncio
    async def test_token_not_expired_with_buffer(self):
        """Test token not expired with buffer time."""
        with self._patch_common_dependencies():
            manager = AsyncTokenManager(self.refresh_token)
            manager._access_token = "valid_token"
            manager._token_expires_at = 9999999999  # Far future

            token = await manager.get_access_token()
            assert token == "valid_token"


class TestAsyncTokenManagerAPIErrors(TestAsyncTokenManager):
    """Test AsyncTokenManager API error handling."""

    @pytest.mark.asyncio
    async def test_refresh_token_request_api_error(self):
        """Test handling of API error response."""

        manager = AsyncTokenManager(self.refresh_token)
        mock_response = self._create_mock_response(400, is_success=False)

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            with patch.object(manager._error_handler, "raise_api_error") as mock_error_handler:
                mock_error_handler.side_effect = BadRequestError(400, "Bad Request")

                with pytest.raises(BadRequestError):
                    await manager._refresh_token_request()

                mock_error_handler.assert_called_once_with(mock_response)
