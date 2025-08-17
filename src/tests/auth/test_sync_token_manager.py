import os
import json
import time
import tempfile
import threading
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

import pytest
from requests.exceptions import ConnectTimeout, ReadTimeout, ConnectionError

from applifting_sdk.auth import SyncTokenManager
from applifting_sdk.exceptions import (
    AppliftingSDKError,
    AppliftingSDKNetworkError,
    AppliftingSDKTimeoutError,
)


class TestSyncTokenManager:
    """Test suite for SyncTokenManager"""

    @pytest.fixture
    def token_manager(self):
        """Create a SyncTokenManager instance for testing"""
        with patch("applifting_sdk.auth.sync_token_manager.user_cache_dir") as mock_cache_dir:
            mock_cache_dir.return_value = tempfile.mkdtemp()
            return SyncTokenManager(refresh_token="test_refresh_token")

    @pytest.fixture
    def mock_auth_response(self):
        """Mock successful auth response"""
        return {"access_token": "test_access_token", "token_type": "Bearer", "expires_in": 3600}

    def test_init(self, token_manager):
        """Test SyncTokenManager initialization"""
        assert token_manager._refresh_token == "test_refresh_token"
        assert token_manager._access_token is None
        assert token_manager._token_expires_at == 0
        assert isinstance(token_manager._lock, threading.Lock)
        assert os.path.exists(os.path.dirname(token_manager._cache_file_path))

    @patch("requests.post")
    def test_get_access_token_fresh_request(self, mock_post, token_manager, mock_auth_response):
        """Test getting access token with fresh API request"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = mock_auth_response
        mock_post.return_value = mock_response

        # Mock AuthResponse model
        with patch("applifting_sdk.models.AuthResponse") as mock_auth_model:
            mock_auth_model.return_value.access_token = "test_access_token"

            token = token_manager.get_access_token()

            assert token == "test_access_token"
            assert token_manager._access_token == "test_access_token"
            assert token_manager._token_expires_at > time.time()
            mock_post.assert_called_once()

    @patch("requests.post")
    def test_get_access_token_cached_valid(self, mock_post, token_manager):
        """Test getting access token from valid cache"""
        # Set up a valid cached token
        token_manager._access_token = "cached_token"
        token_manager._token_expires_at = time.time() + 3600  # Valid for 1 hour

        token = token_manager.get_access_token()

        assert token == "cached_token"
        mock_post.assert_not_called()  # Should not make API call

    def test_is_token_expired(self, token_manager):
        """Test token expiration logic"""
        # Token expired
        token_manager._token_expires_at = time.time() - 100
        assert token_manager._is_token_expired() is True

        # Token valid (considering buffer)
        token_manager._token_expires_at = time.time() + token_manager._buffer_seconds + 100
        assert token_manager._is_token_expired() is False

        # Token within buffer zone (should be considered expired)
        token_manager._token_expires_at = time.time() + token_manager._buffer_seconds - 10
        assert token_manager._is_token_expired() is True

    def test_write_and_read_token_cache(self, token_manager):
        """Test writing and reading token cache"""
        test_token = "test_cache_token"
        test_expires_at = time.time() + 3600

        token_manager._access_token = test_token
        token_manager._token_expires_at = test_expires_at

        # Write to cache
        token_manager._write_token_cache(test_token)

        # Clear memory
        token_manager._access_token = None
        token_manager._token_expires_at = 0

        # Read from cache
        cached_token = token_manager._read_token_cache()

        assert cached_token == test_token
        assert abs(token_manager._token_expires_at - test_expires_at) < 1  # Allow small time difference

    def test_read_token_cache_file_not_exists(self, token_manager):
        """Test reading cache when file doesn't exist"""
        # Ensure cache file doesn't exist
        if os.path.exists(token_manager._cache_file_path):
            os.remove(token_manager._cache_file_path)

        cached_token = token_manager._read_token_cache()
        assert cached_token is None

    def test_read_token_cache_invalid_json(self, token_manager):
        """Test reading cache with invalid JSON"""
        with open(token_manager._cache_file_path, "w") as f:
            f.write("invalid json")

        cached_token = token_manager._read_token_cache()
        assert cached_token is None

    @patch("requests.post")
    def test_get_access_token_from_file_cache(self, mock_post, token_manager):
        """Test getting access token from file cache"""
        # Write valid cache to file
        cache_data = {"access_token": "file_cached_token", "expires_at": time.time() + 3600}

        with open(token_manager._cache_file_path, "w") as f:
            json.dump(cache_data, f)

        token = token_manager.get_access_token()

        assert token == "file_cached_token"
        mock_post.assert_not_called()

    @patch("requests.post")
    def test_refresh_token_request_no_refresh_token(self, mock_post, token_manager):
        """Test refresh token request with no refresh token"""
        token_manager._refresh_token = ""

        with pytest.raises(AppliftingSDKError, match="No refresh token was provided"):
            token_manager.get_access_token()

    @patch("requests.post")
    def test_refresh_token_request_connect_timeout(self, mock_post, token_manager):
        """Test refresh token request with connection timeout"""
        mock_post.side_effect = ConnectTimeout("Connection timeout")

        with pytest.raises(AppliftingSDKTimeoutError, match="Connection timed out"):
            token_manager.get_access_token()

    @patch("requests.post")
    def test_refresh_token_request_read_timeout(self, mock_post, token_manager):
        """Test refresh token request with read timeout"""
        mock_post.side_effect = ReadTimeout("Read timeout")

        with pytest.raises(AppliftingSDKTimeoutError, match="Read timed out"):
            token_manager.get_access_token()

    @patch("requests.post")
    def test_refresh_token_request_connection_error(self, mock_post, token_manager):
        """Test refresh token request with connection error"""
        mock_post.side_effect = ConnectionError("Connection failed")

        with pytest.raises(AppliftingSDKNetworkError):
            token_manager.get_access_token()

    @patch("requests.post")
    def test_refresh_token_request_api_error(self, mock_post, token_manager):
        """Test refresh token request with API error response"""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        # Mock error handler
        token_manager._error_handler.raise_api_error = MagicMock(side_effect=AppliftingSDKError("API Error"))

        with pytest.raises(AppliftingSDKError):
            token_manager.get_access_token()

    @patch("requests.post")
    def test_thread_safety(self, mock_post, token_manager, mock_auth_response):
        """Test thread safety of token manager"""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = mock_auth_response
        mock_post.return_value = mock_response

        # Mock AuthResponse model
        with patch("applifting_sdk.models.AuthResponse") as mock_auth_model:
            mock_auth_model.return_value.access_token = "test_access_token"

            tokens = []
            api_call_count = [0]  # Use list to modify from inner function

            def get_token():
                api_call_count[0] += 1
                return token_manager.get_access_token()

            # Run multiple threads simultaneously
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(get_token) for _ in range(10)]
                tokens = [future.result() for future in futures]

            # All tokens should be the same
            assert all(token == "test_access_token" for token in tokens)

            # API should be called only once due to caching and locking
            assert mock_post.call_count == 1

    @patch("requests.post")
    def test_cache_file_permissions_error(self, mock_post, token_manager):
        """Test handling of file permission errors during cache operations"""
        # Mock file operations to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should not raise exception, just return None
            cached_token = token_manager._read_token_cache()
            assert cached_token is None

    def test_cache_directory_creation(self):
        """Test that cache directory is created during initialization"""
        with patch("applifting_sdk.auth.sync_token_manager.user_cache_dir") as mock_cache_dir:
            test_dir = os.path.join(tempfile.gettempdir(), "test_applifting_cache")
            mock_cache_dir.return_value = test_dir

            # Ensure directory doesn't exist
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

            SyncTokenManager(refresh_token="test_token")

            # Directory should be created
            assert os.path.exists(test_dir)

            # Cleanup
            os.rmdir(test_dir)

    @patch("requests.post")
    def test_multiple_refresh_calls_thread_safety(self, mock_post, token_manager, mock_auth_response):
        """Test that multiple simultaneous refresh calls don't cause issues"""
        call_count = 0

        def mock_post_with_delay(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # Simulate network delay
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.json.return_value = mock_auth_response
            return mock_response

        mock_post.side_effect = mock_post_with_delay

        with patch("applifting_sdk.models.AuthResponse") as mock_auth_model:
            mock_auth_model.return_value.access_token = "test_access_token"

            def get_token():
                return token_manager.get_access_token()

            # Start multiple threads that will all need to refresh
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(get_token) for _ in range(3)]
                tokens = [future.result() for future in futures]

            # All should get the same token
            assert all(token == "test_access_token" for token in tokens)

            # API should be called only once due to locking
            assert call_count == 1
