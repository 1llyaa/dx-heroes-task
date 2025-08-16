"""
Tests for AsyncTokenManager.
"""

import httpx
import pytest
from unittest.mock import AsyncMock, Mock, patch
from applifting_sdk.auth import AsyncTokenManager
from applifting_sdk.exceptions import AppliftingSDKNetworkError, AppliftingSDKTimeoutError, AppliftingSDKError


class TestAsyncTokenManager:
    """Test AsyncTokenManager."""

    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    def test_empty_refresh_token(self, mock_cache_dir, mock_settings):
        """Test initialization with empty refresh token."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"

        manager = AsyncTokenManager("")
        assert manager._refresh_token == ""

    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    def test_none_refresh_token(self, mock_cache_dir, mock_settings):
        """Test initialization with None refresh token."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"

        manager = AsyncTokenManager(None)
        assert manager._refresh_token is None

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    @patch("applifting_sdk.auth.token_manager.os.path.exists")
    @patch("builtins.open")
    async def test_get_access_token_cached(self, mock_open, mock_exists, mock_cache_dir, mock_settings):
        """Test getting cached access token."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"
        mock_exists.return_value = True

        # Mock cache file reading with proper context manager
        mock_file = Mock()
        mock_file.read.return_value = '{"access_token": "cached_token", "expires_at": 9999999999}'
        mock_open.return_value.__enter__.return_value = mock_file
        mock_open.return_value.__exit__.return_value = None

        manager = AsyncTokenManager("refresh_token")
        token = await manager.get_access_token()

        assert token == "cached_token"

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    @patch("applifting_sdk.auth.token_manager.os.path.exists")
    async def test_get_access_token_refresh(self, mock_exists, mock_cache_dir, mock_settings):
        """Test refreshing access token."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"
        mock_exists.return_value = False  # No cache file

        manager = AsyncTokenManager("refresh_token")

        # Mock the HTTP request
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "new_token"}
            mock_client.post = AsyncMock(return_value=mock_response)

            token = await manager.get_access_token()
            assert token == "new_token"

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    async def test_refresh_token_request_success(self, mock_cache_dir, mock_settings):
        """Test successful token refresh request."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"

        manager = AsyncTokenManager("refresh_token")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "new_token"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)

            await manager._refresh_token_request()
            assert manager._access_token == "new_token"

    @pytest.mark.asyncio
    async def test_refresh_token_request_no_refresh_token(self):
        manager = AsyncTokenManager(None)
        mock_response = Mock()
        mock_response.json.side_effect = AppliftingSDKError(
            "No refresh token was provided - create .env file and use load_dotenv()"
        )

        with pytest.raises(AppliftingSDKError) as error:
            await manager._refresh_token_request()
        assert "No refresh token was provided" in str(error.value)
        assert manager._access_token is None

    @pytest.mark.asyncio
    async def test_refresh_token_request_timeout_error(self):
        manager = AsyncTokenManager("refresh_token")

        mock_response = Mock()
        mock_response.side_effect = httpx.ConnectTimeout("Connection timed out")

        with pytest.raises(AppliftingSDKTimeoutError) as error:
            await manager._refresh_token_request()
        assert "Connection timed out" in str(error.value)
        assert manager._access_token is None

    @pytest.mark.asyncio
    async def test_refresh_token_request_read_timeout(self):

        manager = AsyncTokenManager("refresh_token")
        mock_response = Mock()
        mock_response.side_effect = httpx.ReadTimeout("read")

        with pytest.raises(AppliftingSDKTimeoutError) as error:
            await manager._refresh_token_request()
        assert "Read timed out" in str(error.value)
        assert manager._access_token is None

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    async def test_token_expired_with_buffer(self, mock_cache_dir, mock_settings):
        """Test token expiration with buffer time."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"

        manager = AsyncTokenManager("refresh_token")
        manager._access_token = "old_token"
        manager._token_expires_at = 0  # Expired

        # Mock the HTTP request
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "new_token"}
            mock_client.post = AsyncMock(return_value=mock_response)

            token = await manager.get_access_token()
            assert token == "new_token"

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    async def test_token_not_expired_with_buffer(self, mock_cache_dir, mock_settings):
        """Test token not expired with buffer time."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"

        manager = AsyncTokenManager("refresh_token")
        manager._access_token = "valid_token"
        manager._token_expires_at = 9999999999  # Far future

        token = await manager.get_access_token()
        assert token == "valid_token"

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    @patch("applifting_sdk.auth.token_manager.os.path.exists")
    @patch("builtins.open")
    async def test_cache_file_invalid_json(self, mock_open, mock_exists, mock_cache_dir, mock_settings):
        """Test handling invalid JSON in cache file."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"
        mock_exists.return_value = True

        # Mock cache file with invalid JSON
        mock_file = Mock()
        mock_file.read.return_value = "invalid json"
        mock_open.return_value.__enter__.return_value = mock_file
        mock_open.return_value.__exit__.return_value = None

        manager = AsyncTokenManager("refresh_token")

        # Should fall back to refreshing token
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"access_token": "new_token"}
            mock_client.post = AsyncMock(return_value=mock_response)

            token = await manager.get_access_token()
            assert token == "new_token"

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    async def test_cache_file_missing_fields(self, mock_cache_dir, mock_settings):
        """Test cache file with missing fields."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"

        manager = AsyncTokenManager("refresh_token")

        # Mock the _read_token_cache method to return None (missing fields)
        with patch.object(manager, "_read_token_cache", return_value=None):
            # Should fall back to refreshing token
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock()

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"access_token": "new_token"}
                mock_client.post = AsyncMock(return_value=mock_response)

                token = await manager.get_access_token()
                assert token == "new_token"

    @pytest.mark.asyncio
    @patch("applifting_sdk.auth.token_manager.settings")
    @patch("applifting_sdk.auth.token_manager.user_cache_dir")
    async def test_write_token_cache_success(self, mock_cache_dir, mock_settings):
        """Test successful token cache writing."""
        mock_settings.token_expiration_seconds = 300
        mock_settings.token_expiration_buffer_seconds = 5
        mock_settings.base_url = "https://api.test.local"
        mock_cache_dir.return_value = "/tmp/test_cache"

        manager = AsyncTokenManager("refresh_token")
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
