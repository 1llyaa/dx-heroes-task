import pytest
from unittest.mock import patch, Mock, AsyncMock
from applifting_sdk.client import AppliftingSDKClient


class TestAppliftingSDKClient:
    """Test cases for AppliftingSDKClient class."""

    def setup_method(self):
        """Setup fresh test environment for each test."""
        self.refresh_token = "test_refresh_token"


class TestAppliftingSDKClientInitialization(TestAppliftingSDKClient):
    """Test AppliftingSDKClient initialization."""

    @patch("applifting_sdk.client.httpx", None)
    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_initialization_with_requests_backend_explicit(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests
    ):
        """Test client initialization with explicit requests backend."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        assert client.backend == "requests"
        assert not client.is_async
        assert client._token_manager is not None
        assert client._client is not None
        assert client.offers is not None
        assert client.products is not None

    @patch("applifting_sdk.client.requests", None)
    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_initialization_with_httpx_backend_explicit(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx
    ):
        """Test client initialization with explicit httpx backend."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        assert client.backend == "httpx"
        assert client.is_async
        assert client._token_manager is not None
        assert client._client is not None
        assert client.offers is not None
        assert client.products is not None

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_initialization_auto_select_httpx_preferred(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx, mock_requests
    ):
        """Test auto-selection prefers httpx when both are available."""
        client = AppliftingSDKClient(self.refresh_token)

        assert client.backend == "httpx"
        assert client.is_async

    @patch("applifting_sdk.client.httpx", None)
    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_initialization_auto_select_fallback_to_requests(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests
    ):
        """Test auto-selection falls back to requests when httpx unavailable."""
        client = AppliftingSDKClient(self.refresh_token)

        assert client.backend == "requests"
        assert not client.is_async

    @patch("applifting_sdk.client.httpx", None)
    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_empty_refresh_token(self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests):
        """Test initialization with empty refresh token."""
        client = AppliftingSDKClient("", http_backend="requests")

        mock_token_manager.assert_called_once_with(refresh_token="")

    @patch("applifting_sdk.client.httpx", None)
    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_none_refresh_token(self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests):
        """Test initialization with None refresh token."""
        client = AppliftingSDKClient(None, http_backend="requests")

        mock_token_manager.assert_called_once_with(refresh_token=None)

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_component_creation_requests_backend(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests
    ):
        """Test that all components are created for requests backend."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        # Verify all components were instantiated
        mock_token_manager.assert_called_once_with(refresh_token=self.refresh_token)
        mock_client.assert_called_once()
        mock_offers.assert_called_once()
        mock_products.assert_called_once()

        # Verify components are properly assigned
        assert client._token_manager is not None
        assert client._client is not None
        assert client.offers is not None
        assert client.products is not None

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_component_creation_httpx_backend(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx
    ):
        """Test that all components are created for httpx backend."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        # Verify all components were instantiated
        mock_token_manager.assert_called_once_with(refresh_token=self.refresh_token)
        mock_client.assert_called_once()
        mock_offers.assert_called_once()
        mock_products.assert_called_once()

        # Verify components are properly assigned
        assert client._token_manager is not None
        assert client._client is not None
        assert client.offers is not None
        assert client.products is not None


class TestAppliftingSDKClientBackendValidation(TestAppliftingSDKClient):
    """Test AppliftingSDKClient backend validation."""

    @patch("applifting_sdk.client.httpx", None)
    @patch("applifting_sdk.client.requests", None)
    def test_no_backends_available_error(self):
        """Test initialization when no backends are available."""
        with pytest.raises(RuntimeError) as exc_info:
            AppliftingSDKClient(self.refresh_token)

        assert "Install httpx or requests: pip install httpx requests" in str(exc_info.value)

    @patch("applifting_sdk.client.httpx", None)
    @patch("applifting_sdk.client.requests")
    def test_httpx_not_installed_error(self, mock_requests):
        """Test error when httpx backend is requested but not installed."""
        with pytest.raises(RuntimeError) as exc_info:
            AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        assert "httpx not installed: pip install httpx" in str(exc_info.value)

    @patch("applifting_sdk.client.requests", None)
    @patch("applifting_sdk.client.httpx")
    def test_requests_not_installed_error(self, mock_httpx):
        """Test error when requests backend is requested but not installed."""
        with pytest.raises(RuntimeError) as exc_info:
            AppliftingSDKClient(self.refresh_token, http_backend="requests")

        assert "requests not installed: pip install requests" in str(exc_info.value)


class TestAppliftingSDKClientImportHandling(TestAppliftingSDKClient):
    """Test AppliftingSDKClient import error handling."""

    def test_httpx_import_error_handling(self):
        """Test that httpx import errors are handled gracefully."""
        # Simulate ImportError for httpx by patching the import
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "httpx":
                raise ImportError("No module named 'httpx'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Force reimport of the client module to trigger the import error handling
            import importlib
            import applifting_sdk.client

            importlib.reload(applifting_sdk.client)

            # The httpx should be None after import error
            assert applifting_sdk.client.httpx is None

    def test_requests_import_error_handling(self):
        """Test that requests import errors are handled gracefully."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "requests":
                raise ImportError("No module named 'requests'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Force reimport of the client module to trigger the import error handling
            import importlib
            import applifting_sdk.client

            importlib.reload(applifting_sdk.client)

            # The requests should be None after import error
            assert applifting_sdk.client.requests is None


class TestAppliftingSDKClientSyncContextManager(TestAppliftingSDKClient):
    """Test AppliftingSDKClient sync context manager functionality."""

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_sync_context_manager_enter(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests
    ):
        """Test sync context manager __enter__ method."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        with client as ctx_client:
            assert ctx_client is client

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_sync_context_manager_exit(
        self, mock_products, mock_offers, mock_base_client_class, mock_token_manager, mock_requests
    ):
        """Test sync context manager __exit__ method."""
        mock_client_instance = Mock()
        mock_base_client_class.return_value = mock_client_instance

        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        with client:
            pass

        mock_client_instance.close.assert_called_once()

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_sync_context_manager_exit_with_exception(
        self, mock_products, mock_offers, mock_base_client_class, mock_token_manager, mock_requests
    ):
        """Test sync context manager __exit__ method when exception occurs."""
        mock_client_instance = Mock()
        mock_base_client_class.return_value = mock_client_instance

        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        try:
            with client:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should still call close even when exception occurs
        mock_client_instance.close.assert_called_once()

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_async_client_sync_context_manager_error(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx
    ):
        """Test that async client raises error on sync context manager entry."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        with pytest.raises(RuntimeError) as exc_info:
            with client:
                pass

        assert "Use 'async with' for httpx backend" in str(exc_info.value)


class TestAppliftingSDKClientAsyncContextManager(TestAppliftingSDKClient):
    """Test AppliftingSDKClient async context manager functionality."""

    @pytest.mark.asyncio
    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    async def test_async_context_manager_aenter(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx
    ):
        """Test async context manager __aenter__ method."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        # Test that __aenter__ returns the client itself
        result = await client.__aenter__()
        assert result is client

    @pytest.mark.asyncio
    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    async def test_async_context_manager_aexit(
        self, mock_products, mock_offers, mock_base_client_class, mock_token_manager, mock_httpx
    ):
        """Test async context manager __aexit__ method."""
        mock_client_instance = Mock()
        mock_client_instance.aclose = AsyncMock()
        mock_base_client_class.return_value = mock_client_instance

        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        async with client:
            pass

        mock_client_instance.aclose.assert_called_once()

    @pytest.mark.asyncio
    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    async def test_async_context_manager_aexit_with_exception(
        self, mock_products, mock_offers, mock_base_client_class, mock_token_manager, mock_httpx
    ):
        """Test async context manager __aexit__ method when exception occurs."""
        mock_client_instance = Mock()
        mock_client_instance.aclose = AsyncMock()
        mock_base_client_class.return_value = mock_client_instance

        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        try:
            async with client:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should still call aclose even when exception occurs
        mock_client_instance.aclose.assert_called_once()

    @pytest.mark.asyncio
    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    async def test_sync_client_async_context_manager_error(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests
    ):
        """Test that sync client raises error on async context manager entry."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        with pytest.raises(RuntimeError) as exc_info:
            async with client:
                pass

        assert "Use 'with' for requests backend" in str(exc_info.value)


class TestAppliftingSDKClientCleanupMethods(TestAppliftingSDKClient):
    """Test AppliftingSDKClient cleanup methods."""

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_sync_close(self, mock_products, mock_offers, mock_base_client_class, mock_token_manager, mock_requests):
        """Test sync close method."""
        mock_client_instance = Mock()
        mock_base_client_class.return_value = mock_client_instance

        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        client.close()
        mock_client_instance.close.assert_called_once()

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_async_client_sync_close_error(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx
    ):
        """Test that async client raises error on sync close."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        with pytest.raises(RuntimeError) as exc_info:
            client.close()

        assert "Use aclose() for httpx backend" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    async def test_async_aclose(
        self, mock_products, mock_offers, mock_base_client_class, mock_token_manager, mock_httpx
    ):
        """Test async aclose method."""
        mock_client_instance = Mock()
        mock_client_instance.aclose = AsyncMock()
        mock_base_client_class.return_value = mock_client_instance

        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        await client.aclose()
        mock_client_instance.aclose.assert_called_once()

    @pytest.mark.asyncio
    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    async def test_sync_client_async_aclose_error(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests
    ):
        """Test that sync client raises error on async close."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        with pytest.raises(RuntimeError) as exc_info:
            await client.aclose()

        assert "Use close() for requests backend" in str(exc_info.value)


class TestAppliftingSDKClientAPIAccess(TestAppliftingSDKClient):
    """Test AppliftingSDKClient API access."""

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_api_access_sync_backend(self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests):
        """Test that API clients are accessible for sync backend."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        assert client.offers is not None
        assert client.products is not None
        assert hasattr(client, "offers")
        assert hasattr(client, "products")

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_api_access_async_backend(self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx):
        """Test that API clients are accessible for async backend."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        assert client.offers is not None
        assert client.products is not None
        assert hasattr(client, "offers")
        assert hasattr(client, "products")


class TestAppliftingSDKClientAttributes(TestAppliftingSDKClient):
    """Test AppliftingSDKClient attributes and properties."""

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_backend_attribute_requests(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests
    ):
        """Test that backend attribute is set correctly for requests."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        assert hasattr(client, "backend")
        assert client.backend == "requests"

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_backend_attribute_httpx(self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx):
        """Test that backend attribute is set correctly for httpx."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        assert hasattr(client, "backend")
        assert client.backend == "httpx"

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_is_async_attribute_sync(self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests):
        """Test that is_async attribute is set correctly for sync backend."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        assert hasattr(client, "is_async")
        assert client.is_async is False

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_is_async_attribute_async(self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx):
        """Test that is_async attribute is set correctly for async backend."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        assert hasattr(client, "is_async")
        assert client.is_async is True


class TestAppliftingSDKClientComponentIntegration(TestAppliftingSDKClient):
    """Test AppliftingSDKClient component integration."""

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_token_manager_receives_refresh_token_sync(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_requests
    ):
        """Test that sync token manager is initialized with refresh token."""
        refresh_token = "test_refresh_token_123"

        client = AppliftingSDKClient(refresh_token, http_backend="requests")

        mock_token_manager.assert_called_once_with(refresh_token=refresh_token)

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_token_manager_receives_refresh_token_async(
        self, mock_products, mock_offers, mock_client, mock_token_manager, mock_httpx
    ):
        """Test that async token manager is initialized with refresh token."""
        refresh_token = "test_refresh_token_456"

        client = AppliftingSDKClient(refresh_token, http_backend="httpx")

        mock_token_manager.assert_called_once_with(refresh_token=refresh_token)

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_client_receives_token_manager_sync(
        self, mock_products, mock_offers, mock_base_client, mock_token_manager, mock_requests
    ):
        """Test that sync base client is initialized with token manager."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        # Verify that base client was called with token manager
        args, kwargs = mock_base_client.call_args
        assert "token_manager" in kwargs
        assert kwargs["token_manager"] is not None

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_client_receives_token_manager_async(
        self, mock_products, mock_offers, mock_base_client, mock_token_manager, mock_httpx
    ):
        """Test that async base client is initialized with token manager."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        # Verify that base client was called with token manager
        args, kwargs = mock_base_client.call_args
        assert "token_manager" in kwargs
        assert kwargs["token_manager"] is not None

    @patch("applifting_sdk.client.requests")
    @patch("applifting_sdk.client.SyncTokenManager")
    @patch("applifting_sdk.client.SyncBaseClient")
    @patch("applifting_sdk.client.SyncOffersAPI")
    @patch("applifting_sdk.client.SyncProductsAPI")
    def test_api_clients_receive_base_client_sync(
        self, mock_products, mock_offers, mock_base_client, mock_token_manager, mock_requests
    ):
        """Test that sync API clients are initialized with base client."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="requests")

        # Verify that API clients were called with base client
        for mock_api in [mock_offers, mock_products]:
            args, kwargs = mock_api.call_args
            assert "client" in kwargs
            assert kwargs["client"] is not None

    @patch("applifting_sdk.client.httpx")
    @patch("applifting_sdk.client.AsyncTokenManager")
    @patch("applifting_sdk.client.AsyncBaseClient")
    @patch("applifting_sdk.client.AsyncOffersAPI")
    @patch("applifting_sdk.client.AsyncProductsAPI")
    def test_api_clients_receive_base_client_async(
        self, mock_products, mock_offers, mock_base_client, mock_token_manager, mock_httpx
    ):
        """Test that async API clients are initialized with base client."""
        client = AppliftingSDKClient(self.refresh_token, http_backend="httpx")

        # Verify that API clients were called with base client
        for mock_api in [mock_offers, mock_products]:
            args, kwargs = mock_api.call_args
            assert "client" in kwargs
            assert kwargs["client"] is not None
