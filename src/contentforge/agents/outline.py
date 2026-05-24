"""Outline Agent — Creates structured content outlines from research."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class OutlineAgent(BaseAgent):
    name = "outline"
    description = "Creates structured outlines with section hierarchy and word allocation"

    system_prompt = """You are the Outline Agent in a content creation pipeline.

Your role:
1. Take research data and create a well-structured article outline
2. Allocate word count per section proportionally to importance
3. Ensure logical flow: hook → context → body → conclusion
4. Add SEO keyword placement suggestions per section
5. Include transition notes between sections

Output format (JSON):
{
    "title": "...",
    "meta_description": "...",
    "target_word_count": N,
    "sections": [
        {
            "heading": "...",
            "subheadings": [...],
            "word_allocation": N,
            "key_points": [...],
            "seo_keywords": [...],
            "transition_note": "..."
        }
    ],
    "estimated_reading_time": "X min",
    "content_type": "article|guide|listicle|comparison"
}

Aim for 6-10 sections with clear hierarchy."""

    async def execute(
        self, research_data: str = "", target_words: int = 2000, **kwargs
    ) -> AgentResult:
        """Create an outline from research data."""
        prompt = f"""Based on the following research data, create a detailed article outline.

Target word count: {target_words} words

Research Data:
{research_data}

Create a structured outline with:
- Compelling title and meta description
- 6-10 sections with word allocation
- Key points per section
- SEO keyword suggestions
- Logical flow with transitions

Return as structured JSON."""

        response = await self._call_mimo(prompt)

        return AgentResult(
            agent_name=self.name,
            content=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            reasoning=response.reasoning_content,
            metadata={
                "target_words": target_words,
                "output_length": len(response.content),
            },
        )
