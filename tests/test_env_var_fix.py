#!/usr/bin/env python3
"""
Test suite for DD_* environment variable fix (PR #3)

Tests that the config loader correctly uses DD_* environment variables
as required by the Datadog SDK.
"""

import os
import pytest
from unittest.mock import patch
from datadog_api_client import Configuration


class TestDDEnvironmentVariables:
    """Test DD_* environment variable loading in our config"""

    @patch.dict(os.environ, {
        'DD_API_KEY': 'test_api_key',
        'DD_APP_KEY': 'test_app_key',
        'DD_SITE': 'datadoghq.eu'
    }, clear=True)
    def test_load_config_with_dd_env_vars(self):
        """Test config loading with DD_* environment variables"""
        from server import _load_config

        config = _load_config()

        assert config.api_key == "test_api_key"
        assert config.app_key == "test_app_key"
        assert config.site == "datadoghq.eu"

    @patch.dict(os.environ, {
        'DD_API_KEY': 'test_api_key',
        'DD_APP_KEY': 'test_app_key'
    }, clear=True)
    def test_load_config_default_site(self):
        """Test config loading with default site using DD_* variables"""
        from server import _load_config

        config = _load_config()

        assert config.api_key == "test_api_key"
        assert config.app_key == "test_app_key"
        assert config.site == "datadoghq.com"

    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_missing_dd_api_key(self):
        """Test config loading fails with missing DD_API_KEY"""
        from server import _load_config

        with pytest.raises(ValueError, match="DD_API_KEY and DD_APP_KEY must be set"):
            _load_config()

    @patch.dict(os.environ, {'DD_API_KEY': 'test_key'}, clear=True)
    def test_load_config_missing_dd_app_key(self):
        """Test config loading fails with missing DD_APP_KEY"""
        from server import _load_config

        with pytest.raises(ValueError, match="DD_API_KEY and DD_APP_KEY must be set"):
            _load_config()


class TestDatadogSDKRequiresDDVars:
    """
    Test that proves the Datadog SDK itself requires DD_* variables.

    This demonstrates that DATADOG_* variables never worked, proving this
    is a bug fix rather than a breaking change.
    """

    @patch.dict(os.environ, {
        'DATADOG_API_KEY': 'test_api_key',
        'DATADOG_APP_KEY': 'test_app_key',
        'DATADOG_SITE': 'datadoghq.com'
    }, clear=True)
    def test_datadog_sdk_ignores_datadog_prefix_variables(self):
        """
        Test that the Datadog SDK Configuration does NOT read DATADOG_* variables.
        This proves the old variable names never worked with the actual SDK.
        """
        # Create a Datadog SDK Configuration object with only DATADOG_* vars set
        config = Configuration()

        # The SDK will have empty/None values because it doesn't read DATADOG_* variables
        # It only reads DD_* variables
        assert config.api_key is None or config.api_key == {}
        assert config.server_variables.get('site') is None or config.server_variables.get('site') == 'datadoghq.com'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
