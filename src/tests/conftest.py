"""
Pytest configuration and shared fixtures for the Applifting SDK test suite.
"""


import pytest

# -------- pytest configuration --------


def pytest_configure(config):
    """Configure pytest with custom markers."""
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
    import applifting_sdk.auth.async_token_manager as tm

    monkeypatch.setattr(tm, "user_cache_dir", lambda *args, **kwargs: str(tmp_path), raising=True)
