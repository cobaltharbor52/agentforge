"""Integration tests for the pipeline orchestrator."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from contentforge.core.config import ContentForgeConfig
from contentforge.core.mimo_client import ChatResponse, TokenUsage
from contentforge.pipeline.orchestrator import PipelineOrchestrator, PipelineResult


def make_response(content: str, prompt_tokens=500, completion_tokens=300) -> ChatResponse:
    return ChatResponse(
        content=content,
        usage=TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
        model="mimo-v2.5-pro",
        latency_ms=100,
    )


AGENT_RESPONSES = {
    "research": json.dumps(
        {
            "topic": "AI Healthcare",
            "key_subtopics": [{"title": "Diagnosis", "key_facts": ["fact1"]}],
        }
    ),
    "outline": json.dumps(
        {
            "title": "AI in Healthcare",
            "sections": [{"heading": "Intro", "word_allocation": 200}],
        }
    ),
    "writer": "# AI in Healthcare\n\nA comprehensive guide.",
    "seo": json.dumps({"seo_score": 85, "keyword_analysis": {}}),
    "editor": "# AI in Healthcare (Edited)\n\nPolished guide.",
    "quality": json.dumps({"overall_score": 90, "pass_threshold": True}),
    "publisher": json.dumps(
        {
            "formats": {"markdown": "content"},
            "metadata": {"title": "AI Healthcare"},
        }
    ),
}


class TestPipelineOrchestrator:
    @pytest.fixture
    def config(self, tmp_path):
        return ContentForgeConfig(
            output_dir=str(tmp_path / "output"),
            cache_dir=str(tmp_path / "cache"),
        )

    @pytest.mark.asyncio
    async def test_full_pipeline_success(self, config):
        """Test complete 8-agent pipeline run."""
        responses = [
            make_response(AGENT_RESPONSES["research"]),
            make_response(AGENT_RESPONSES["outline"]),
            make_response(AGENT_RESPONSES["writer"]),
            make_response(AGENT_RESPONSES["seo"]),
            make_response(AGENT_RESPONSES["editor"]),
            make_response(AGENT_RESPONSES["quality"]),
            make_response(AGENT_RESPONSES["publisher"]),
        ]

        call_count = {"n": 0}

        async def mock_chat(*args, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            return responses[idx]

        with patch("contentforge.pipeline.orchestrator.MiMoClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.chat = AsyncMock(side_effect=mock_chat)
            mock_instance.total_usage = TokenUsage()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            orchestrator = PipelineOrchestrator(config)
            result = await orchestrator.run("AI in Healthcare")

        assert result.ok
        assert result.total_tokens > 0
        assert "research" in result.agent_results
        assert "writer" in result.agent_results

    @pytest.mark.asyncio
    async def test_pipeline_with_translation(self, config):
        """Test pipeline with translation enabled."""
        config.pipeline.enable_translation = True
        config.pipeline.target_languages = ["zh"]

        responses = [
            make_response(AGENT_RESPONSES["research"]),
            make_response(AGENT_RESPONSES["outline"]),
            make_response(AGENT_RESPONSES["writer"]),
            make_response(AGENT_RESPONSES["seo"]),
            make_response(AGENT_RESPONSES["editor"]),
            make_response(AGENT_RESPONSES["quality"]),
            make_response("# AI Guide Chinese"),
            make_response(AGENT_RESPONSES["publisher"]),
        ]

        call_count = {"n": 0}

        async def mock_chat(*args, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            return responses[idx]

        with patch("contentforge.pipeline.orchestrator.MiMoClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.chat = AsyncMock(side_effect=mock_chat)
            mock_instance.total_usage = TokenUsage()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            orchestrator = PipelineOrchestrator(config)
            result = await orchestrator.run("AI in Healthcare")

        assert "zh" in result.translations

    @pytest.mark.asyncio
    async def test_pipeline_failure_at_research(self, config):
        """Test pipeline handles agent failure gracefully."""

        async def mock_chat(*args, **kwargs):
            raise Exception("API connection failed")

        with patch("contentforge.pipeline.orchestrator.MiMoClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.chat = AsyncMock(side_effect=mock_chat)
            mock_instance.total_usage = TokenUsage()
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            orchestrator = PipelineOrchestrator(config)
            result = await orchestrator.run("Test Topic")

        assert result.status == "failed"

    def test_agent_list(self, config):
        """Test agent list returns all 8 agents."""
        orchestrator = PipelineOrchestrator(config)
        agents = orchestrator.get_agent_list()
        assert len(agents) == 8
        names = [a["name"] for a in agents]
        assert "research" in names
        assert "publisher" in names


class TestPipelineResult:
    def test_ok_status(self):
        r = PipelineResult(status="success", article="content", total_tokens=1000)
        assert r.ok is True

    def test_failed_status(self):
        r = PipelineResult(status="failed")
        assert r.ok is False

    def test_summary(self):
        r = PipelineResult(
            status="success",
            article="# Article\nContent here",
            total_tokens=5000,
            pipeline_duration_s=12.5,
        )
        summary = r.summary()
        assert summary["total_tokens"] == 5000
        assert summary["word_count"] > 0

    def test_summary_translations(self):
        r = PipelineResult(translations={"zh": "content", "ms": "content"})
        summary = r.summary()
        assert "zh" in summary["translations"]
