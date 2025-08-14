import httpx
import pytest
from unittest.mock import AsyncMock, Mock, patch
from applifting_sdk.auth import AsyncTokenManager


@patch('applifting_sdk.auth.token_manager.settings')
@patch('applifting_sdk.auth.token_manager.user_cache_dir')
def test_initialization(mock_cache_dir, mock_settings):
    """Test token manager initialization."""
    mock_settings.token_expiration_seconds = 300
    mock_settings.token_expiration_buffer_seconds = 5
    mock_settings.base_url = "https://api.test.local"
    mock_cache_dir.return_value = "/tmp/test_cache"

    manager = AsyncTokenManager("test_token")
    assert manager._refresh_token == "test_token"
    assert manager._expiration_seconds == 300
    assert manager._buffer_seconds == 5

@patch('applifting_sdk.auth.token_manager.settings')
@patch('applifting_sdk.auth.token_manager.user_cache_dir')
def test_empty_refresh_token(mock_cache_dir, mock_settings):
    """Test initialization with empty refresh token."""
    mock_settings.token_expiration_seconds = 300
    mock_settings.token_expiration_buffer_seconds = 5
    mock_settings.base_url = "https://api.test.local"
    mock_cache_dir.return_value = "/tmp/test_cache"

    manager = AsyncTokenManager("")
    assert manager._refresh_token == ""

@patch('applifting_sdk.auth.token_manager.settings')
@patch('applifting_sdk.auth.token_manager.user_cache_dir')
def test_none_refresh_token(mock_cache_dir, mock_settings):
    """Test initialization with None refresh token."""
    mock_settings.token_expiration_seconds = 300
    mock_settings.token_expiration_buffer_seconds = 5
    mock_settings.base_url = "https://api.test.local"
    mock_cache_dir.return_value = "/tmp/test_cache"

    manager = AsyncTokenManager(None)
    assert manager._refresh_token is None