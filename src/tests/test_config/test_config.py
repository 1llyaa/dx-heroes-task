"""
Tests for configuration settings.
"""

from unittest.mock import patch

from applifting_sdk.config import Settings, settings


class TestSettings:
    """Test Settings class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = Settings()
        assert config.base_url == "https://python.exercise.applifting.cz/"
        assert config.refresh_token is None
        assert config.token_expiration_seconds == 300
        assert config.token_expiration_buffer_seconds == 5

    def test_custom_values(self):
        """Test custom configuration values."""
        config = Settings(
            base_url="https://api.custom.com/",
            refresh_token="custom_token",
            token_expiration_seconds=600,
            token_expiration_buffer_seconds=10,
        )
        assert config.base_url == "https://api.custom.com/"
        assert config.refresh_token == "custom_token"
        assert config.token_expiration_seconds == 600
        assert config.token_expiration_buffer_seconds == 10

    @patch.dict("os.environ", {"REFRESH_TOKEN": "env_token", "BASE_URL": "https://api.env.com/"})
    def test_environment_variables(self):
        """Test loading from environment variables."""
        config = Settings()
        assert config.base_url == "https://api.env.com/"
        assert config.refresh_token == "env_token"


class TestGlobalSettings:
    """Test global settings instance."""

    def test_global_settings_defaults(self):
        """Test global settings have correct defaults."""
        assert settings.base_url == "https://api.test.local"
        assert settings.refresh_token is None
        assert settings.token_expiration_seconds == 10
        assert settings.token_expiration_buffer_seconds == 2
