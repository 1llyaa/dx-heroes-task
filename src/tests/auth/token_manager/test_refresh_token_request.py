import httpx
import pytest

from unittest.mock import AsyncMock, Mock, patch
from applifting_sdk.auth import AsyncTokenManager
from applifting_sdk.exceptions import AppliftingSDKNetworkError, AppliftingSDKTimeoutError, AppliftingSDKError


@pytest.mark.asyncio
@patch('applifting_sdk.auth.token_manager.settings')
@patch('applifting_sdk.auth.token_manager.user_cache_dir')
async def test_refresh_token_request_success(mock_cache_dir, mock_settings):
    """Test successful token refresh request."""
    mock_settings.token_expiration_seconds = 300
    mock_settings.token_expiration_buffer_seconds = 5
    mock_settings.base_url = "https://api.test.local"
    mock_cache_dir.return_value = "/tmp/test_cache"

    manager = AsyncTokenManager("refresh_token")

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "new_token"}

    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        await manager._refresh_token_request()
        assert manager._access_token == "new_token"

@pytest.mark.asyncio
async def test_refresh_token_request_no_refresh_token():
    manager = AsyncTokenManager(None)
    mock_response = Mock()
    mock_response.json.side_effect = AppliftingSDKError("No refresh token was provided - create .env file and use load_dotenv()")

    with pytest.raises(AppliftingSDKError) as error:
        await manager._refresh_token_request()
    assert "No refresh token was provided" in str(error.value)
    assert manager._access_token is None


@pytest.mark.asyncio
async def test_refresh_token_request_timeout_error():
    manager = AsyncTokenManager("refresh_token")

    mock_response = Mock()
    mock_response.side_effect = httpx.ConnectTimeout("Connection timed out")


    with pytest.raises(AppliftingSDKTimeoutError) as error:
        await manager._refresh_token_request()
    assert "Connection timed out" in str(error.value)
    assert manager._access_token is None

@pytest.mark.asyncio
async def test_refresh_token_request_read_timeout():

    manager = AsyncTokenManager("refresh_token")
    mock_response = Mock()
    mock_response.side_effect = httpx.ReadTimeout("read")


    with pytest.raises(AppliftingSDKTimeoutError) as error:
        await manager._refresh_token_request()
    assert "Read timed out" in str(error.value)
    assert manager._access_token is None