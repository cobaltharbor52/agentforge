"""Configuration management for ContentForge pipeline.

ContentForge speaks the OpenAI-compatible ``/chat/completions`` protocol, so it
works with any provider that exposes that API: OpenAI, OpenRouter, Ollama,
local llama.cpp servers, Xiaomi MiMo Token Plan, and more. Pick a provider via
``LLMConfig(provider=...)`` or point ``base_url`` at any compatible endpoint.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, model_validator

# Provider presets: base_url, auth header style, default model, and the env
# vars used to populate api_key / base_url when they aren't set explicitly.
# auth_style is "bearer" (Authorization: Bearer) or "api-key" (api-key header).
PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "mimo": {
        "base_url": "https://token-plan-sgp.xiaomimimo.com/v1",
        "auth_style": "api-key",
        "model": "mimo-v2.5-pro",
        "env_key": "MIMO_API_KEY",
        "env_base": "MIMO_BASE_URL",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "auth_style": "bearer",
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "env_base": "OPENAI_BASE_URL",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "auth_style": "bearer",
        "model": "openai/gpt-4o-mini",
        "env_key": "OPENROUTER_API_KEY",
        "env_base": "OPENROUTER_BASE_URL",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "auth_style": "bearer",
        "model": "llama3.1",
        "env_key": "OLLAMA_API_KEY",
        "env_base": "OLLAMA_BASE_URL",
    },
}

DEFAULT_PROVIDER = "mimo"


class LLMConfig(BaseModel):
    """Connection settings for any OpenAI-compatible chat completions endpoint.

    Empty ``api_key`` / ``base_url`` / ``model`` / ``auth_style`` fields are
    resolved from the selected provider preset (and its env vars) after init.
    """

    provider: str = DEFAULT_PROVIDER
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    auth_style: str = ""  # "bearer" | "api-key" — resolved from provider if blank
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0

    @model_validator(mode="after")
    def _resolve_provider_defaults(self) -> "LLMConfig":
        preset = PROVIDER_PRESETS.get(self.provider, PROVIDER_PRESETS[DEFAULT_PROVIDER])
        if not self.api_key:
            self.api_key = os.environ.get(preset["env_key"], "")
        if not self.base_url:
            self.base_url = os.environ.get(preset["env_base"], preset["base_url"])
        if not self.model:
            self.model = preset["model"]
        if not self.auth_style:
            self.auth_style = preset["auth_style"]
        return self

    @property
    def headers(self) -> dict[str, str]:
        """Auth + content headers, matching the provider's expected auth style."""
        headers = {"Content-Type": "application/json"}
        if self.auth_style == "bearer":
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            headers["api-key"] = self.api_key
        return headers


class MiMoConfig(LLMConfig):
    """Backward-compatible alias defaulting to the Xiaomi MiMo Token Plan API.

    Retained so existing configs/tests keep working. New code should prefer
    :class:`LLMConfig` with an explicit ``provider``.
    """

    provider: str = "mimo"


class PipelineConfig(BaseModel):
    """Pipeline execution settings."""

    topic: str = ""
    target_word_count: int = 2000
    language: str = "en"
    output_format: str = "markdown"
    seo_enabled: bool = True
    quality_threshold: float = 0.8
    max_iterations: int = 3
    enable_translation: bool = False
    target_languages: list[str] = Field(default_factory=lambda: ["zh", "ms"])
    publish_targets: list[str] = Field(default_factory=lambda: ["markdown"])


class AgentConfig(BaseModel):
    """Per-agent configuration overrides."""

    name: str
    enabled: bool = True
    model_override: Optional[str] = None
    temperature_override: Optional[float] = None
    max_tokens_override: Optional[int] = None
    system_prompt_override: Optional[str] = None


class ContentForgeConfig(BaseModel):
    """Root configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    pipeline: PipelineConfig = Field(default_factory=PipelineConfig)
    agents: list[AgentConfig] = Field(default_factory=list)
    log_level: str = "INFO"
    output_dir: str = "./output"
    cache_dir: str = "./.cache"

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_mimo_key(cls, data):
        """Map a legacy top-level ``mimo:`` block onto ``llm`` for old configs."""
        if isinstance(data, dict) and "mimo" in data and "llm" not in data:
            data = dict(data)
            data["llm"] = data.pop("mimo")
        return data

    @property
    def mimo(self) -> LLMConfig:
        """Deprecated alias for :attr:`llm` (kept for backward compatibility)."""
        return self.llm

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ContentForgeConfig":
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    @classmethod
    def from_env(cls) -> "ContentForgeConfig":
        return cls(llm=LLMConfig())

    def get_agent_config(self, name: str) -> AgentConfig:
        for agent in self.agents:
            if agent.name == name:
                return agent
        return AgentConfig(name=name)
