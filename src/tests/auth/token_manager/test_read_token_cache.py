import httpx
import pytest

from unittest.mock import AsyncMock, Mock, patch
from applifting_sdk.auth import AsyncTokenManager
from applifting_sdk.exceptions import AppliftingSDKNetworkError, AppliftingSDKTimeoutError, AppliftingSDKError

@pytest.mark.asyncio
@patch('applifting_sdk.auth.token_manager.settings')
@patch('applifting_sdk.auth.token_manager.user_cache_dir')
@patch('applifting_sdk.auth.token_manager.os.path.exists')
@patch('builtins.open')
async def test_cache_file_invalid_json(mock_open, mock_exists, mock_cache_dir, mock_settings):
    """Test handling invalid JSON in cache file."""
    mock_settings.token_expiration_seconds = 300
    mock_settings.token_expiration_buffer_seconds = 5
    mock_settings.base_url = "https://api.test.local"
    mock_cache_dir.return_value = "/tmp/test_cache"
    mock_exists.return_value = True

    # Mock cache file with invalid JSON
    mock_file = Mock()
    mock_file.read.return_value = 'invalid json'
    mock_open.return_value.__enter__.return_value = mock_file
    mock_open.return_value.__exit__.return_value = None

    manager = AsyncTokenManager("refresh_token")

    # Should fall back to refreshing token
    with patch('httpx.AsyncClient') as mock_client_class:
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