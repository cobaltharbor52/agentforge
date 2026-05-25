"""Unit tests for configuration management."""

import os
import pytest
import tempfile
import yaml

from contentforge.core.config import (
    AgentConfig,
    ContentForgeConfig,
    MiMoConfig,
    PipelineConfig,
)


class TestMiMoConfig:
    def test_default_values(self):
        config = MiMoConfig(api_key="test")
        assert config.model == "mimo-v2.5-pro"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.timeout == 120
        assert config.max_retries == 3

    def test_custom_values(self):
        config = MiMoConfig(
            api_key="custom-key",
            model="mimo-v2.5-lite",
            max_tokens=2048,
            temperature=0.5,
        )
        assert config.api_key == "custom-key"
        assert config.model == "mimo-v2.5-lite"
        assert config.max_tokens == 2048
        assert config.temperature == 0.5

    def test_headers_use_api_key_not_bearer(self):
        """MiMo Token Plan uses api-key header, NOT Authorization: Bearer."""
        config = MiMoConfig(api_key="my-secret-key")
        headers = config.headers
        assert "api-key" in headers
        assert headers["api-key"] == "my-secret-key"
        assert "Authorization" not in headers

    def test_headers_content_type(self):
        config = MiMoConfig(api_key="test")
        assert config.headers["Content-Type"] == "application/json"

    def test_base_url_default(self):
        config = MiMoConfig(api_key="test")
        assert "token-plan-sgp.xiaomimimo.com" in config.base_url

    def test_base_url_custom(self):
        config = MiMoConfig(api_key="test", base_url="https://custom.api.com/v1")
        assert config.base_url == "https://custom.api.com/v1"

    def test_from_env_uses_env_vars(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "env-key-123")
        monkeypatch.setenv("MIMO_BASE_URL", "https://env.api.com/v1")
        config = MiMoConfig()
        assert config.api_key == "env-key-123"
        assert config.base_url == "https://env.api.com/v1"


class TestPipelineConfig:
    def test_defaults(self):
        config = PipelineConfig()
        assert config.target_word_count == 2000
        assert config.language == "en"
        assert config.seo_enabled is True
        assert config.quality_threshold == 0.8
        assert config.max_iterations == 3

    def test_translation_defaults(self):
        config = PipelineConfig()
        assert config.enable_translation is False
        assert "zh" in config.target_languages
        assert "ms" in config.target_languages

    def test_publish_targets(self):
        config = PipelineConfig(publish_targets=["html", "wordpress"])
        assert "html" in config.publish_targets
        assert "wordpress" in config.publish_targets


class TestAgentConfig:
    def test_defaults(self):
        config = AgentConfig(name="test-agent")
        assert config.name == "test-agent"
        assert config.enabled is True
        assert config.model_override is None

    def test_overrides(self):
        config = AgentConfig(
            name="writer",
            temperature_override=0.9,
            max_tokens_override=8192,
        )
        assert config.temperature_override == 0.9
        assert config.max_tokens_override == 8192


class TestContentForgeConfig:
    def test_default_config(self):
        config = ContentForgeConfig()
        assert config.mimo.model == "mimo-v2.5-pro"
        assert config.log_level == "INFO"
        assert config.output_dir == "./output"

    def test_from_yaml(self):
        data = {
            "mimo": {"api_key": "yaml-key", "model": "mimo-v2.5-pro"},
            "pipeline": {"target_word_count": 3000},
            "log_level": "DEBUG",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            f.flush()
            config = ContentForgeConfig.from_yaml(f.name)

        assert config.mimo.api_key == "yaml-key"
        assert config.pipeline.target_word_count == 3000
        assert config.log_level == "DEBUG"
        os.unlink(f.name)

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "env-test-key")
        config = ContentForgeConfig.from_env()
        assert config.mimo.api_key == "env-test-key"

    def test_get_agent_config_existing(self):
        config = ContentForgeConfig(
            agents=[AgentConfig(name="writer", temperature_override=0.9)]
        )
        agent_config = config.get_agent_config("writer")
        assert agent_config.temperature_override == 0.9

    def test_get_agent_config_missing_returns_default(self):
        config = ContentForgeConfig()
        agent_config = config.get_agent_config("nonexistent")
        assert agent_config.name == "nonexistent"
        assert agent_config.enabled is True
