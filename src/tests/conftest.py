"""
Pytest configuration and shared fixtures for the Applifting SDK test suite.
"""

import json
import re
from typing import Callable, Dict, Tuple, Any
import httpx
import pytest
from contextlib import contextmanager

# -------- pytest configuration --------


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual functions and classes")
    config.addinivalue_line("markers", "integration: Integration tests for component interactions")
    config.addinivalue_line("markers", "auth: Tests related to authentication and token management")
    config.addinivalue_line("markers", "http: Tests related to HTTP client functionality")
    config.addinivalue_line("markers", "models: Tests related to data models and validation")
    config.addinivalue_line("markers", "resources: Tests related to API resources (offers, products)")
    config.addinivalue_line("markers", "exceptions: Tests related to exception handling")


def pytest_collection_modifyitems(config, items):
    """Automatically add markers based on test file location."""
    for item in items:
        # Add markers based on test file path
        if "test_auth" in str(item.fspath):
            item.add_marker(pytest.mark.auth)
        elif "test_http" in str(item.fspath):
            item.add_marker(pytest.mark.http)
        elif "test_models" in str(item.fspath):
            item.add_marker(pytest.mark.models)
        elif "test_resources" in str(item.fspath):
            item.add_marker(pytest.mark.resources)
        elif "test_exceptions" in str(item.fspath):
            item.add_marker(pytest.mark.exceptions)
        elif "test_helpers" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_client" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Default to unit test if no other marker
        if not list(item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# -------- helpers --------


def build_mock_transport(
    routes: Dict[Tuple[str, str], httpx.Response] | Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    """
    Create a MockTransport. You can pass:
      - a dict mapping (METHOD, PATH) -> Response
      - or a callable(request) -> Response
    """
    if callable(routes):
        return httpx.MockTransport(routes)

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method.upper(), request.url.path)
        if key in routes:
            return routes[key]
        # Allow simple path params: register /offers GETs via regex-like startswith
        for (m, p), resp in routes.items():
            if m == request.method.upper() and (p.endswith("*") and request.url.path.startswith(p[:-1])):
                return resp
        return httpx.Response(404, json={"detail": "Not Found (unrouted)"})

    return httpx.MockTransport(handler)


# -------- fixtures --------


@pytest.fixture
def base_url() -> str:
    # Use a deterministic fake base URL
    return "https://api.test.local"


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch, base_url, tmp_path):
    # Make your SDK settings deterministic for tests
    # Adjust the import path to your config module:
    # applifting_sdk.config.settings
    from applifting_sdk import config as cfg

    # If using pydantic Settings instance:
    try:
        monkeypatch.setattr(cfg.settings, "base_url", base_url, raising=True)
        monkeypatch.setattr(cfg.settings, "token_expiration_seconds", 10, raising=True)
        monkeypatch.setattr(cfg.settings, "token_expiration_buffer_seconds", 2, raising=True)
    except AttributeError:
        # If config defines module-level constants instead of a Settings instance
        monkeypatch.setattr(cfg, "BASE_URL", base_url, raising=False)

    # Ensure token cache goes into tmp_path by patching platformdirs.user_cache_dir
    import applifting_sdk.auth.token_manager as tm

    monkeypatch.setattr(tm, "user_cache_dir", lambda *args, **kwargs: str(tmp_path), raising=True)


@pytest.fixture
def auth_ok_response() -> httpx.Response:
    return httpx.Response(201, json={"access_token": "T1"})


@pytest.fixture
def auth_401_response() -> httpx.Response:
    return httpx.Response(401, text="Unauthorized")


@pytest.fixture
def auth_422_response() -> httpx.Response:
    return httpx.Response(
        422,
        json={"detail": [{"loc": ["header", "Bearer"], "msg": "Invalid token", "type": "value_error"}]},
    )


@pytest.fixture
def make_transport():
    """
    Factory to create a MockTransport with simple route dict or callable.
    """

    def _make(routes) -> httpx.MockTransport:
        return build_mock_transport(routes)

    return _make


@pytest.fixture
def patch_httpx_client(monkeypatch):
    """
    Context manager fixture:
    with patch_httpx_client(transport):
        ... code that constructs httpx.AsyncClient ...

    Všechny nově vytvořené AsyncClient instance použijí náš 'transport'.
    """

    @contextmanager
    def _ctx(transport: httpx.MockTransport):
        original_ctor = httpx.AsyncClient

        def _ctor(*args, **kwargs):
            # zachovej původní kwargs, jen injektuj transport
            kwargs["transport"] = transport
            return original_ctor(*args, **kwargs)

        # patchni konstruktor
        monkeypatch.setattr(httpx, "AsyncClient", _ctor, raising=True)
        try:
            yield
        finally:
            # vrať původní stav
            monkeypatch.setattr(httpx, "AsyncClient", original_ctor, raising=True)

    return _ctx


# -------- additional fixtures --------


@pytest.fixture
def mock_httpx_async_client(monkeypatch):
    """Mock httpx.AsyncClient to avoid real HTTP requests."""
    mock_client = httpx.AsyncClient()
    mock_client.request = httpx.AsyncClient.request
    mock_client.aclose = httpx.AsyncClient.aclose

    def _mock_async_client(*args, **kwargs):
        return mock_client

    monkeypatch.setattr(httpx, "AsyncClient", _mock_async_client)
    return mock_client


@pytest.fixture
def sample_error_responses():
    """Dictionary of common error responses for testing."""
    return {
        400: {"detail": "Bad Request"},
        401: {"detail": "Unauthorized"},
        403: {"detail": "Forbidden"},
        404: {"detail": "Not Found"},
        409: {"detail": "Conflict"},
        422: {"detail": "Validation Error"},
        429: {"detail": "Too Many Requests"},
        500: {"detail": "Internal Server Error"},
        502: {"detail": "Bad Gateway"},
        503: {"detail": "Service Unavailable"},
    }
