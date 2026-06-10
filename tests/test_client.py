"""
Tests for ainative-openai package.

Covers:
- OpenAI client initialization (explicit key, env vars, saved config, auto-provision)
- AsyncOpenAI client initialization
- Base URL configuration
- Provisioning logic (success, failure, config persistence)
- Key resolution priority chain
- Package public API
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ainative_openai import API_BASE, AsyncOpenAI, OpenAI, __version__, provision
from ainative_openai.client import _resolve_key
from ainative_openai.provision import (
    CONFIG_FILE,
    INSTANT_DB_URL,
    _load_config,
    _save_config,
    load_saved_key,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_env():
    """Remove AINative/OpenAI env vars."""
    for var in ("AINATIVE_API_KEY", "OPENAI_API_KEY", "AINATIVE_BASE_URL"):
        os.environ.pop(var, None)


# ---------------------------------------------------------------------------
# Key resolution
# ---------------------------------------------------------------------------

class TestResolveKey:
    """Test the _resolve_key priority chain."""

    def setup_method(self):
        _clean_env()

    def teardown_method(self):
        _clean_env()

    def test_explicit_key_takes_priority(self):
        os.environ["AINATIVE_API_KEY"] = "env_key"
        assert _resolve_key("explicit_key") == "explicit_key"

    def test_ainative_env_var_fallback(self):
        os.environ["AINATIVE_API_KEY"] = "ainative_env"
        assert _resolve_key(None) == "ainative_env"

    def test_openai_env_var_fallback(self):
        os.environ["OPENAI_API_KEY"] = "openai_env"
        assert _resolve_key(None) == "openai_env"

    def test_ainative_env_takes_priority_over_openai(self):
        os.environ["AINATIVE_API_KEY"] = "ainative_env"
        os.environ["OPENAI_API_KEY"] = "openai_env"
        assert _resolve_key(None) == "ainative_env"

    @patch("ainative_openai.client.load_saved_key", return_value="saved_key")
    def test_saved_key_fallback(self, mock_load):
        assert _resolve_key(None) == "saved_key"

    @patch("ainative_openai.client.load_saved_key", return_value=None)
    @patch("ainative_openai.client.provision", return_value="provisioned_key")
    def test_auto_provision_fallback(self, mock_provision, mock_load):
        assert _resolve_key(None) == "provisioned_key"
        mock_provision.assert_called_once()


# ---------------------------------------------------------------------------
# OpenAI client
# ---------------------------------------------------------------------------

class TestOpenAIClient:
    """Test OpenAI subclass initialization."""

    def setup_method(self):
        _clean_env()

    def teardown_method(self):
        _clean_env()

    def test_init_with_explicit_key(self):
        client = OpenAI(api_key="test_key_123")
        assert client.api_key == "test_key_123"

    def test_init_with_explicit_base_url(self):
        client = OpenAI(api_key="k", base_url="http://localhost:8000/v1")
        assert str(client.base_url).rstrip("/") == "http://localhost:8000/v1"

    def test_default_base_url(self):
        client = OpenAI(api_key="k")
        assert API_BASE in str(client.base_url)

    def test_base_url_from_env(self):
        os.environ["AINATIVE_BASE_URL"] = "http://custom:9000/v1"
        client = OpenAI(api_key="k")
        assert "custom:9000" in str(client.base_url)

    def test_env_key_used(self):
        os.environ["AINATIVE_API_KEY"] = "from_env"
        client = OpenAI()
        assert client.api_key == "from_env"

    @patch("ainative_openai.client.provision", return_value="auto_key")
    @patch("ainative_openai.client.load_saved_key", return_value=None)
    def test_auto_provisions_when_no_key(self, mock_load, mock_provision):
        client = OpenAI()
        assert client.api_key == "auto_key"
        mock_provision.assert_called_once()

    def test_passes_kwargs_to_parent(self):
        client = OpenAI(api_key="k", timeout=60.0)
        assert client.timeout == 60.0


# ---------------------------------------------------------------------------
# AsyncOpenAI client
# ---------------------------------------------------------------------------

class TestAsyncOpenAIClient:
    """Test AsyncOpenAI subclass initialization."""

    def setup_method(self):
        _clean_env()

    def teardown_method(self):
        _clean_env()

    def test_init_with_explicit_key(self):
        client = AsyncOpenAI(api_key="async_key")
        assert client.api_key == "async_key"

    def test_default_base_url(self):
        client = AsyncOpenAI(api_key="k")
        assert API_BASE in str(client.base_url)

    @patch("ainative_openai.client.provision", return_value="async_auto")
    @patch("ainative_openai.client.load_saved_key", return_value=None)
    def test_auto_provisions(self, mock_load, mock_provision):
        client = AsyncOpenAI()
        assert client.api_key == "async_auto"


# ---------------------------------------------------------------------------
# Provisioning
# ---------------------------------------------------------------------------

class TestProvision:
    """Test auto-provisioning via instant-db."""

    @patch("ainative_openai.provision.requests.post")
    @patch("ainative_openai.provision._save_config")
    def test_provision_success(self, mock_save, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "api_key": "zdb_new_abc",
            "claim_url": "https://ainative.studio/claim?token=xyz",
            "project_id": "proj_123",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        key = provision()
        assert key == "zdb_new_abc"
        mock_post.assert_called_once_with(
            INSTANT_DB_URL,
            json={"agree_terms": True},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        mock_save.assert_called_once()

    @patch("ainative_openai.provision.requests.post")
    @patch("ainative_openai.provision._save_config")
    def test_provision_uses_key_field(self, mock_save, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"key": "zdb_alt_456"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        key = provision()
        assert key == "zdb_alt_456"

    @patch("ainative_openai.provision.requests.post")
    def test_provision_failure_raises(self, mock_post):
        mock_post.side_effect = Exception("Connection refused")
        with pytest.raises(RuntimeError, match="Failed to auto-provision"):
            provision()

    @patch("ainative_openai.provision.requests.post")
    def test_provision_no_key_in_response(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"project_id": "abc"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        with pytest.raises(RuntimeError, match="Failed to auto-provision"):
            provision()


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------

class TestConfigPersistence:
    """Test ~/.ainative/config.json load/save."""

    @patch("ainative_openai.provision.CONFIG_FILE")
    def test_load_config_missing_file(self, mock_file):
        mock_file.exists.return_value = False
        assert _load_config() == {}

    @patch("ainative_openai.provision.CONFIG_FILE")
    def test_load_config_valid_json(self, mock_file):
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = '{"api_key": "saved_123"}'
        assert _load_config() == {"api_key": "saved_123"}

    @patch("ainative_openai.provision.CONFIG_FILE")
    def test_load_config_corrupted_json(self, mock_file):
        mock_file.exists.return_value = True
        mock_file.read_text.return_value = "not json"
        assert _load_config() == {}

    @patch("ainative_openai.provision.CONFIG_DIR")
    @patch("ainative_openai.provision.CONFIG_FILE")
    def test_save_config(self, mock_file, mock_dir):
        _save_config({"api_key": "new_key"})
        mock_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_file.write_text.assert_called_once()

    @patch("ainative_openai.provision._load_config", return_value={"api_key": "cached_key"})
    def test_load_saved_key_returns_value(self, mock_config):
        assert load_saved_key() == "cached_key"


# ---------------------------------------------------------------------------
# Package API
# ---------------------------------------------------------------------------

class TestPackageAPI:
    """Test public API surface."""

    def test_version(self):
        assert __version__ == "0.1.0"

    def test_openai_exported(self):
        import ainative_openai
        assert hasattr(ainative_openai, "OpenAI")

    def test_async_openai_exported(self):
        import ainative_openai
        assert hasattr(ainative_openai, "AsyncOpenAI")

    def test_provision_exported(self):
        import ainative_openai
        assert hasattr(ainative_openai, "provision")

    def test_api_base_exported(self):
        import ainative_openai
        assert hasattr(ainative_openai, "API_BASE")
        assert "ainative.studio" in ainative_openai.API_BASE

    def test_openai_is_subclass(self):
        from openai import OpenAI as _OpenAI
        assert issubclass(OpenAI, _OpenAI)

    def test_async_openai_is_subclass(self):
        from openai import AsyncOpenAI as _AsyncOpenAI
        assert issubclass(AsyncOpenAI, _AsyncOpenAI)
