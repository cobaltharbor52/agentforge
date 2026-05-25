"""Unit tests for all 8 agents."""

import json
import pytest
from unittest.mock import AsyncMock

from contentforge.agents.base import BaseAgent, AgentResult
from contentforge.agents.research import ResearchAgent
from contentforge.agents.outline import OutlineAgent
from contentforge.agents.writer import WriterAgent
from contentforge.agents.seo import SEOAgent
from contentforge.agents.editor import EditorAgent
from contentforge.agents.translator import TranslatorAgent
from contentforge.agents.quality import QualityAgent
from contentforge.agents.publisher import PublisherAgent
from contentforge.agents import AGENT_REGISTRY, get_agent
from contentforge.core.mimo_client import ChatResponse, TokenUsage


def make_test_response(content='{"test": "data"}', prompt=500, comp=300):
    return ChatResponse(
        content=content,
        usage=TokenUsage(prompt_tokens=prompt, completion_tokens=comp, total_tokens=prompt+comp),
        model="mimo-v2.5-pro",
        latency_ms=100.0,
    )


class TestAgentResult:
    def test_default_status(self):
        r = AgentResult(agent_name="test")
        assert r.status == "success"
        assert r.ok is True

    def test_failed_status(self):
        r = AgentResult(agent_name="test", status="failed")
        assert r.ok is False

    def test_partial_is_not_ok(self):
        r = AgentResult(agent_name="test", status="partial")
        assert r.ok is False  # only 'success' is ok

    def test_metadata_default_empty(self):
        r = AgentResult(agent_name="test")
        assert r.metadata == {}

    def test_error_field(self):
        r = AgentResult(agent_name="test", status="failed", error="timeout")
        assert r.error == "timeout"

    def test_tokens_used(self):
        r = AgentResult(agent_name="test", tokens_used=1500)
        assert r.tokens_used == 1500

    def test_latency_tracking(self):
        r = AgentResult(agent_name="test", latency_ms=250.5)
        assert r.latency_ms == 250.5

    def test_reasoning_field(self):
        r = AgentResult(agent_name="test", reasoning="step by step...")
        assert r.reasoning == "step by step..."


class TestAgentRegistry:
    def test_all_8_registered(self):
        assert len(AGENT_REGISTRY) == 8

    def test_expected_names(self):
        expected = {"research", "outline", "writer", "seo", "editor", "translator", "quality", "publisher"}
        assert set(AGENT_REGISTRY.keys()) == expected

    def test_get_valid_agent(self, config, mock_client, tracker):
        for name in AGENT_REGISTRY:
            agent = get_agent(name, config=config, client=mock_client, tracker=tracker)
            assert agent.name == name

    def test_get_invalid_raises(self, config, mock_client, tracker):
        with pytest.raises(ValueError, match="Unknown agent"):
            get_agent("nonexistent", config=config, client=mock_client, tracker=tracker)

    def test_all_subclass_base(self, config, mock_client, tracker):
        for name in AGENT_REGISTRY:
            agent = get_agent(name, config=config, client=mock_client, tracker=tracker)
            assert isinstance(agent, BaseAgent)


class TestResearchAgent:
    def test_name(self, config, mock_client, tracker):
        a = ResearchAgent(config=config, client=mock_client, tracker=tracker)
        assert a.name == "research"

    def test_has_system_prompt(self, config, mock_client, tracker):
        a = ResearchAgent(config=config, client=mock_client, tracker=tracker)
        assert "Research Agent" in a.system_prompt

    @pytest.mark.asyncio
    async def test_execute_returns_result(self, config, mock_client, tracker):
        mock_client.chat = AsyncMock(return_value=make_test_response(
            '{"topic": "AI", "key_subtopics": [{"title": "ML"}]}'
        ))
        a = ResearchAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(topic="AI in Healthcare")
        assert result.ok
        assert result.metadata["topic"] == "AI in Healthcare"

    @pytest.mark.asyncio
    async def test_run_handles_error(self, config, mock_client, tracker):
        mock_client.chat = AsyncMock(side_effect=Exception("API down"))
        a = ResearchAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.run(topic="Test")
        assert result.status == "failed"
        assert "API down" in result.error


class TestOutlineAgent:
    def test_name(self, config, mock_client, tracker):
        a = OutlineAgent(config=config, client=mock_client, tracker=tracker)
        assert a.name == "outline"

    @pytest.mark.asyncio
    async def test_execute_with_research(self, config, mock_client, tracker):
        mock_client.chat = AsyncMock(return_value=make_test_response(
            '{"title": "Guide", "sections": []}'
        ))
        a = OutlineAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(research_data="data", target_words=2000)
        assert result.ok
        assert result.metadata["target_words"] == 2000


class TestWriterAgent:
    def test_name(self, config, mock_client, tracker):
        a = WriterAgent(config=config, client=mock_client, tracker=tracker)
        assert a.name == "writer"

    @pytest.mark.asyncio
    async def test_execute_produces_content(self, config, mock_client, tracker):
        mock_client.chat = AsyncMock(return_value=make_test_response(
            "# AI Guide\n\nComprehensive content here."
        ))
        a = WriterAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(outline="Outline", research_data="Research")
        assert result.ok
        assert result.metadata["word_count"] > 0


class TestSEOAgent:
    def test_name(self, config, mock_client, tracker):
        a = SEOAgent(config=config, client=mock_client, tracker=tracker)
        assert a.name == "seo"

    @pytest.mark.asyncio
    async def test_execute_analyzes(self, config, mock_client, tracker):
        mock_client.chat = AsyncMock(return_value=make_test_response(
            '{"seo_score": 85}'
        ))
        a = SEOAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(content="# Article", target_keywords=["AI"])
        assert result.ok
        assert result.metadata["target_keywords"] == ["AI"]


class TestEditorAgent:
    def test_name(self, config, mock_client, tracker):
        a = EditorAgent(config=config, client=mock_client, tracker=tracker)
        assert a.name == "editor"

    @pytest.mark.asyncio
    async def test_execute_refines(self, config, mock_client, tracker):
        mock_client.chat = AsyncMock(return_value=make_test_response(
            "# Refined Article\n\nPolished."
        ))
        a = EditorAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(content="Draft", seo_recommendations="Tips")
        assert result.ok


class TestTranslatorAgent:
    def test_name(self, config, mock_client, tracker):
        a = TranslatorAgent(config=config, client=mock_client, tracker=tracker)
        assert a.name == "translator"

    @pytest.mark.asyncio
    async def test_execute_translates(self, config, mock_client, tracker):
        mock_client.chat = AsyncMock(return_value=make_test_response(
            "# AI Guide\n\nChinese content."
        ))
        a = TranslatorAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(content="# AI", target_language="zh")
        assert result.ok
        assert result.metadata["target_language"] == "zh"

    @pytest.mark.asyncio
    async def test_preserves_keywords(self, config, mock_client, tracker):
        mock_client.chat = AsyncMock(return_value=make_test_response(
            "MiMo is great"
        ))
        a = TranslatorAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(
            content="text", target_language="ms", preserve_keywords=["MiMo"]
        )
        assert result.ok


class TestQualityAgent:
    def test_name(self, config, mock_client, tracker):
        a = QualityAgent(config=config, client=mock_client, tracker=tracker)
        assert a.name == "quality"

    @pytest.mark.asyncio
    async def test_execute_passes_threshold(self, config, mock_client, tracker):
        report = json.dumps({"overall_score": 90, "pass_threshold": True})
        mock_client.chat = AsyncMock(return_value=make_test_response(report))
        a = QualityAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(content="Good article", threshold=0.8)
        assert result.metadata["passes_threshold"] is True

    @pytest.mark.asyncio
    async def test_execute_fails_threshold(self, config, mock_client, tracker):
        report = json.dumps({"overall_score": 50, "pass_threshold": False})
        mock_client.chat = AsyncMock(return_value=make_test_response(report))
        a = QualityAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(content="Bad article", threshold=0.8)
        assert result.metadata["passes_threshold"] is False


class TestPublisherAgent:
    def test_name(self, config, mock_client, tracker):
        a = PublisherAgent(config=config, client=mock_client, tracker=tracker)
        assert a.name == "publisher"

    @pytest.mark.asyncio
    async def test_execute_creates_files(self, config, mock_client, tracker):
        output = json.dumps({"formats": {"markdown": "content"}, "metadata": {"title": "T"}})
        mock_client.chat = AsyncMock(return_value=make_test_response(output))
        a = PublisherAgent(config=config, client=mock_client, tracker=tracker)
        result = await a.execute(content="# Article", title="Test", publish_targets=["md"])
        assert result.ok


class TestBaseAgentConfig:
    def test_system_prompt_override(self, config, mock_client, tracker):
        from contentforge.core.config import AgentConfig
        config.agents = [AgentConfig(name="research", system_prompt_override="Custom")]
        a = ResearchAgent(config=config, client=mock_client, tracker=tracker)
        assert a.effective_system_prompt == "Custom"

    def test_default_system_prompt(self, config, mock_client, tracker):
        a = ResearchAgent(config=config, client=mock_client, tracker=tracker)
        assert "Research Agent" in a.effective_system_prompt
