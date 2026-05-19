"""Tests for configuration management."""

import os
from unittest.mock import patch

from mimo_agents.core.config import ModelConfig, Settings


def test_model_config_defaults():
    config = ModelConfig(model_id="test-model")
    assert config.model_id == "test-model"
    assert config.max_tokens == 8192
    assert config.temperature == 0.7
    assert config.top_p == 0.9


def test_settings_defaults():
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()
        assert settings.api_key == ""
        assert settings.base_url == "https://api.xiaomimimo.com/v1"
        assert settings.reasoning_model.model_id == "MiMo-V2.5-Pro"
        assert settings.multimodal_model.model_id == "MiMo-V2.5"
        assert settings.tts_model.model_id == "MiMo-V2.5-TTS"


def test_settings_from_env():
    env_vars = {
        "MIMO_API_KEY": "test-key-123",
        "MIMO_BASE_URL": "https://custom.api.com/v1",
    }
    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings.from_env()
        assert settings.api_key == "test-key-123"
        assert settings.base_url == "https://custom.api.com/v1"


def test_settings_validate_missing_key():
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()
        errors = settings.validate()
        assert len(errors) == 1
        assert "MIMO_API_KEY" in errors[0]


def test_settings_validate_with_key():
    with patch.dict(os.environ, {"MIMO_API_KEY": "key123"}, clear=True):
        settings = Settings.from_env()
        errors = settings.validate()
        assert len(errors) == 0
