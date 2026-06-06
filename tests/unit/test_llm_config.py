"""Unit tests for multi-backend LLM configuration.

Covers the provider-agnostic LLMConfig: preset resolution, bearer vs api-key
auth styles, env-var fallbacks, and backward-compatible MiMoConfig behaviour.
"""

from contentforge.core.config import (
    DEFAULT_PROVIDER,
    PROVIDER_PRESETS,
    ContentForgeConfig,
    LLMConfig,
    MiMoConfig,
)


class TestProviderPresets:
    def test_known_providers_present(self):
        for provider in (
            "mimo",
            "openai",
            "openrouter",
            "ollama",
            "groq",
            "deepseek",
            "together",
            "mistral",
        ):
            assert provider in PROVIDER_PRESETS

    def test_default_provider_is_mimo(self):
        assert DEFAULT_PROVIDER == "mimo"


class TestLLMConfigPresetResolution:
    def test_openai_preset(self):
        config = LLMConfig(provider="openai", api_key="sk-test")
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4o-mini"
        assert config.auth_style == "bearer"

    def test_openrouter_preset(self):
        config = LLMConfig(provider="openrouter", api_key="or-test")
        assert "openrouter.ai" in config.base_url
        assert config.auth_style == "bearer"

    def test_ollama_preset(self):
        config = LLMConfig(provider="ollama")
        assert "localhost:11434" in config.base_url
        assert config.model == "llama3.1"

    def test_unknown_provider_falls_back_to_default(self):
        config = LLMConfig(provider="does-not-exist", api_key="x")
        assert "xiaomimimo.com" in config.base_url  # mimo default

    def test_groq_preset(self):
        config = LLMConfig(provider="groq", api_key="gsk-test")
        assert "api.groq.com" in config.base_url
        assert config.auth_style == "bearer"
        assert config.model == "llama-3.3-70b-versatile"

    def test_deepseek_preset(self):
        config = LLMConfig(provider="deepseek", api_key="sk-test")
        assert "api.deepseek.com" in config.base_url
        assert config.auth_style == "bearer"
        assert config.model == "deepseek-chat"

    def test_together_preset(self):
        config = LLMConfig(provider="together", api_key="tg-test")
        assert "api.together.xyz" in config.base_url
        assert config.auth_style == "bearer"

    def test_mistral_preset(self):
        config = LLMConfig(provider="mistral", api_key="ms-test")
        assert "api.mistral.ai" in config.base_url
        assert config.auth_style == "bearer"

    def test_explicit_values_override_preset(self):
        config = LLMConfig(
            provider="openai",
            base_url="https://proxy.local/v1",
            model="custom-model",
        )
        assert config.base_url == "https://proxy.local/v1"
        assert config.model == "custom-model"


class TestAuthStyles:
    def test_bearer_auth_header(self):
        config = LLMConfig(provider="openai", api_key="sk-abc")
        headers = config.headers
        assert headers["Authorization"] == "Bearer sk-abc"
        assert "api-key" not in headers

    def test_api_key_auth_header(self):
        config = LLMConfig(provider="mimo", api_key="mimo-secret")
        headers = config.headers
        assert headers["api-key"] == "mimo-secret"
        assert "Authorization" not in headers

    def test_explicit_auth_style_override(self):
        config = LLMConfig(provider="mimo", api_key="k", auth_style="bearer")
        assert config.headers["Authorization"] == "Bearer k"


class TestEnvResolution:
    def test_openai_env_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
        config = LLMConfig(provider="openai")
        assert config.api_key == "sk-from-env"

    def test_openrouter_env_base(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-env")
        monkeypatch.setenv("OPENROUTER_BASE_URL", "https://env.openrouter/v1")
        config = LLMConfig(provider="openrouter")
        assert config.api_key == "or-env"
        assert config.base_url == "https://env.openrouter/v1"


class TestMiMoBackwardCompat:
    def test_mimo_config_defaults_to_mimo_provider(self):
        config = MiMoConfig(api_key="test")
        assert config.provider == "mimo"
        assert config.model == "mimo-v2.5-pro"
        assert "xiaomimimo.com" in config.base_url
        assert config.headers["api-key"] == "test"

    def test_root_config_mimo_property_aliases_llm(self):
        config = ContentForgeConfig()
        assert config.mimo is config.llm

    def test_legacy_mimo_yaml_block_maps_to_llm(self):
        config = ContentForgeConfig(**{"mimo": {"api_key": "legacy", "model": "mimo-v2.5-pro"}})
        assert config.llm.api_key == "legacy"
        assert config.mimo.api_key == "legacy"

    def test_new_llm_yaml_block(self):
        config = ContentForgeConfig(**{"llm": {"provider": "openai", "api_key": "sk-x"}})
        assert config.llm.provider == "openai"
        assert config.llm.auth_style == "bearer"
