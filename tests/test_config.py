"""
tests/test_config.py
~~~~~~~~~~~~~~~~~~~~
Unit tests for codesage.config
"""

import os
import pytest
from unittest.mock import patch


def test_config_defaults():
    """Config should load sensible defaults when no env vars are set."""
    with patch.dict(os.environ, {}, clear=False):
        from importlib import reload
        import codesage.config as cfg_module
        reload(cfg_module)
        cfg = cfg_module.Config()
        assert cfg.ollama_base_url.startswith("http")
        assert cfg.max_tokens >= 256
        assert cfg.output_format in ("rich", "plain", "json")


def test_config_env_override():
    """Custom env vars should override defaults."""
    env = {
        "OLLAMA_BASE_URL": "http://custom:11434",
        "OLLAMA_MODEL": "codellama",
        "MAX_TOKENS": "512",
        "OUTPUT_FORMAT": "json",
    }
    with patch.dict(os.environ, env):
        from importlib import reload
        import codesage.config as cfg_module
        reload(cfg_module)
        cfg = cfg_module.Config()
        assert cfg.ollama_base_url == "http://custom:11434"
        assert cfg.model == "codellama"
        assert cfg.max_tokens == 512
        assert cfg.output_format == "json"


def test_config_validate_bad_url():
    """validate() should raise on malformed URL."""
    from codesage.config import Config
    cfg = Config()
    cfg.ollama_base_url = "ftp://bad-url"
    with pytest.raises(ValueError, match="OLLAMA_BASE_URL"):
        cfg.validate()


def test_config_validate_bad_tokens():
    """validate() should raise if max_tokens is too small."""
    from codesage.config import Config
    cfg = Config()
    cfg.max_tokens = 10
    with pytest.raises(ValueError, match="MAX_TOKENS"):
        cfg.validate()


def test_config_validate_bad_format():
    """validate() should raise on unknown output format."""
    from codesage.config import Config
    cfg = Config()
    cfg.output_format = "xml"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="OUTPUT_FORMAT"):
        cfg.validate()
