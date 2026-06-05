"""Pipeline orchestrator — coordinates all 8 agents in sequence."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ..agents import AGENT_REGISTRY, get_agent
from ..agents.base import AgentResult
from ..core.config import ContentForgeConfig
from ..core.mimo_client import MiMoClient
from ..core.token_tracker import TokenTracker

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Final result from the complete pipeline."""

    status: str = "success"
    article: str = ""
    research: str = ""
    outline: str = ""
    seo_analysis: str = ""
    quality_report: str = ""
    publisher_output: str = ""
    translations: dict[str, str] = field(default_factory=dict)
    agent_results: dict[str, AgentResult] = field(default_factory=dict)
    metrics_path: str = ""
    total_tokens: int = 0
    pipeline_duration_s: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status == "success"

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "total_tokens": self.total_tokens,
            "pipeline_duration_s": round(self.pipeline_duration_s, 2),
            "agents_run": list(self.agent_results.keys()),
            "article_length": len(self.article),
            "word_count": len(self.article.split()),
            "translations": list(self.translations.keys()),
            "metrics_path": self.metrics_path,
        }


class PipelineOrchestrator:
    """Coordinates all 8 ContentForge agents in sequence.

    Pipeline flow:
    1. Research → gather information
    2. Outline → structure content
    3. Writer → generate draft
    4. SEO → analyze optimization opportunities
    5. Editor → refine and polish (incorporates SEO suggestions)
    6. Quality → fact-check and score
    7. Translator → adapt to target languages (if enabled)
    8. Publisher → format and export

    Supports iterative refinement: if Quality score < threshold,
    re-run Editor → Quality loop up to max_iterations times.
    """

    AGENT_ORDER = [
        "research",
        "outline",
        "writer",
        "seo",
        "editor",
        "quality",
        "translator",
        "publisher",
    ]

    def __init__(self, config: ContentForgeConfig):
        self.config = config
        self.tracker = TokenTracker(output_dir=config.output_dir)
        self._client: Optional[MiMoClient] = None

    async def run(self, topic: str, **kwargs) -> PipelineResult:
        """Execute the full pipeline for a given topic."""
        result = PipelineResult()

        self.tracker.start_pipeline()

        async with MiMoClient(self.config.mimo) as client:
            self._client = client

            try:
                # Step 1: Research
                logger.info("[Pipeline] Step 1/8: Research")
                research_agent = get_agent(
                    "research", config=self.config, client=client, tracker=self.tracker
                )
                research_result = await research_agent.run(topic=topic)
                result.agent_results["research"] = research_result
                result.research = research_result.content

                if not research_result.ok:
                    result.status = "failed"
                    result.total_tokens = self.tracker.total_tokens
                    return result

                # Step 2: Outline
                logger.info("[Pipeline] Step 2/8: Outline")
                outline_agent = get_agent(
                    "outline", config=self.config, client=client, tracker=self.tracker
                )
                outline_result = await outline_agent.run(
                    research_data=research_result.content,
                    target_words=self.config.pipeline.target_word_count,
                )
                result.agent_results["outline"] = outline_result
                result.outline = outline_result.content

                if not outline_result.ok:
                    result.status = "failed"
                    result.total_tokens = self.tracker.total_tokens
                    return result

                # Step 3: Writer
                logger.info("[Pipeline] Step 3/8: Writer")
                writer_agent = get_agent(
                    "writer", config=self.config, client=client, tracker=self.tracker
                )
                writer_result = await writer_agent.run(
                    outline=outline_result.content,
                    research_data=research_result.content,
                    language=self.config.pipeline.language,
                )
                result.agent_results["writer"] = writer_result
                current_content = writer_result.content

                # Step 4: SEO Analysis
                logger.info("[Pipeline] Step 4/8: SEO")
                seo_agent = get_agent(
                    "seo", config=self.config, client=client, tracker=self.tracker
                )
                seo_result = await seo_agent.run(content=current_content)
                result.agent_results["seo"] = seo_result
                result.seo_analysis = seo_result.content

                # Step 5 + 6: Editor → Quality loop
                for iteration in range(self.config.pipeline.max_iterations):
                    logger.info(f"[Pipeline] Step 5/8: Editor (iteration {iteration + 1})")
                    editor_agent = get_agent(
                        "editor", config=self.config, client=client, tracker=self.tracker
                    )
                    editor_result = await editor_agent.run(
                        content=current_content,
                        seo_recommendations=seo_result.content,
                    )
                    result.agent_results["editor"] = editor_result
                    current_content = editor_result.content

                    logger.info(f"[Pipeline] Step 6/8: Quality (iteration {iteration + 1})")
                    quality_agent = get_agent(
                        "quality", config=self.config, client=client, tracker=self.tracker
                    )
                    quality_result = await quality_agent.run(
                        content=current_content,
                        threshold=self.config.pipeline.quality_threshold,
                        title=topic,
                    )
                    result.agent_results["quality"] = quality_result
                    result.quality_report = quality_result.content

                    # Check if quality passes threshold
                    quality_score = quality_result.metadata.get("overall_score", 0)
                    threshold = self.config.pipeline.quality_threshold * 100
                    if quality_score >= threshold:
                        logger.info(
                            f"[Pipeline] Quality score {quality_score} >= {threshold}, passing"
                        )
                        break
                    elif iteration < self.config.pipeline.max_iterations - 1:
                        logger.info(
                            f"[Pipeline] Quality score {quality_score} < {threshold}, "
                            f"re-editing (iteration {iteration + 2})"
                        )

                result.article = current_content

                # Step 7: Translation (if enabled)
                if self.config.pipeline.enable_translation:
                    logger.info("[Pipeline] Step 7/8: Translation")
                    translator_agent = get_agent(
                        "translator", config=self.config, client=client, tracker=self.tracker
                    )
                    for lang in self.config.pipeline.target_languages:
                        trans_result = await translator_agent.run(
                            content=current_content,
                            target_language=lang,
                        )
                        result.translations[lang] = trans_result.content
                        result.agent_results[f"translator_{lang}"] = trans_result
                else:
                    logger.info("[Pipeline] Step 7/8: Translation (skipped, disabled)")

                # Step 8: Publisher
                logger.info("[Pipeline] Step 8/8: Publisher")
                publisher_agent = get_agent(
                    "publisher", config=self.config, client=client, tracker=self.tracker
                )
                publisher_result = await publisher_agent.run(
                    content=current_content,
                    title=topic,
                    publish_targets=self.config.pipeline.publish_targets,
                    output_dir=self.config.output_dir,
                )
                result.agent_results["publisher"] = publisher_result
                result.publisher_output = publisher_result.content

            except Exception as e:
                logger.error(f"[Pipeline] Fatal error: {e}")
                result.status = "failed"
            finally:
                self.tracker.end_pipeline()
                result.total_tokens = self.tracker.total_tokens
                result.pipeline_duration_s = self.tracker.pipeline_duration_s
                result.metrics_path = str(self.tracker.save())

        return result

    def get_agent_list(self) -> list[dict[str, str]]:
        """Return list of all available agents with descriptions."""
        return [
            {"name": name, "description": cls.description} for name, cls in AGENT_REGISTRY.items()
        ]
