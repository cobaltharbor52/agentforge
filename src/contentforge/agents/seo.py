"""SEO Agent — Optimizes content for search engines."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class SEOAgent(BaseAgent):
    name = "seo"
    description = "Analyzes and optimizes content for search engine visibility"

    system_prompt = """You are the SEO Agent in a content creation pipeline.

Your role:
1. Analyze content for SEO effectiveness
2. Suggest keyword density improvements
3. Optimize title and meta description for CTR
4. Check heading hierarchy (H1 → H2 → H3)
5. Recommend internal/external linking opportunities
6. Identify featured snippet opportunities
7. Suggest image alt-text recommendations

Output format (JSON):
{
    "seo_score": 0-100,
    "keyword_analysis": {
        "primary_keyword": "...",
        "secondary_keywords": [...],
        "keyword_density": "...%",
        "recommendations": [...]
    },
    "title_optimization": {
        "current": "...",
        "suggested": "...",
        "reason": "..."
    },
    "meta_description": {
        "current": "...",
        "optimized": "...",
        "char_count": N
    },
    "heading_structure": {
        "issues": [...],
        "suggestions": [...]
    },
    "featured_snippet_candidates": [...],
    "internal_link_suggestions": [...],
    "image_alt_suggestions": [...],
    "overall_recommendations": [...]
}"""

    async def execute(
        self, content: str = "", target_keywords: list[str] | None = None, **kwargs
    ) -> AgentResult:
        """Analyze content for SEO and provide optimization recommendations."""
        keywords_str = ", ".join(target_keywords) if target_keywords else "auto-detect"

        prompt = f"""Analyze the following content for SEO effectiveness.

Target Keywords: {keywords_str}

CONTENT:
{content}

Provide:
1. SEO score (0-100)
2. Keyword density analysis
3. Title and meta description optimization
4. Heading structure review
5. Featured snippet opportunities
6. Internal linking suggestions
7. Image alt-text recommendations

Return as structured JSON."""

        response = await self._call_mimo(prompt)

        return AgentResult(
            agent_name=self.name,
            content=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            reasoning=response.reasoning_content,
            metadata={
                "target_keywords": target_keywords or [],
                "content_length": len(content),
            },
        )
