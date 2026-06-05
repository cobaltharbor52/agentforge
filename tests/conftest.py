"""Shared test fixtures for ContentForge test suite."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from contentforge.core.config import ContentForgeConfig, MiMoConfig, PipelineConfig
from contentforge.core.mimo_client import ChatResponse, MiMoClient, TokenUsage
from contentforge.core.token_tracker import TokenTracker


@pytest.fixture
def mimo_config() -> MiMoConfig:
    return MiMoConfig(
        api_key="test-key-123",
        base_url="https://test-api.example.com/v1",
        model="mimo-v2.5-pro",
        max_tokens=4096,
        temperature=0.7,
    )


@pytest.fixture
def pipeline_config() -> PipelineConfig:
    return PipelineConfig(
        topic="Test Topic",
        target_word_count=1000,
        language="en",
        output_format="markdown",
        seo_enabled=True,
        quality_threshold=0.8,
        max_iterations=2,
        enable_translation=False,
        target_languages=["zh"],
    )


@pytest.fixture
def config(mimo_config, pipeline_config) -> ContentForgeConfig:
    return ContentForgeConfig(
        mimo=mimo_config,
        pipeline=pipeline_config,
        output_dir="/tmp/contentforge_test_output",
    )


@pytest.fixture
def tracker() -> TokenTracker:
    return TokenTracker(output_dir="/tmp/contentforge_test_output")


@pytest.fixture
def mock_response() -> ChatResponse:
    return ChatResponse(
        content='{"test": "response"}',
        usage=TokenUsage(
            prompt_tokens=500,
            completion_tokens=300,
            total_tokens=800,
            cached_tokens=100,
        ),
        model="mimo-v2.5-pro",
        finish_reason="stop",
        latency_ms=150.0,
    )


@pytest.fixture
def mock_client(mock_response) -> AsyncMock:
    client = AsyncMock(spec=MiMoClient)
    client.chat = AsyncMock(return_value=mock_response)
    client.stream_chunks = AsyncMock()
    client.total_usage = TokenUsage()
    return client
