"""Research Agent — Gathers and synthesizes information for content creation."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class ResearchAgent(BaseAgent):
    name = "research"
    description = "Gathers background information, key facts, and expert perspectives"

    system_prompt = """You are the Research Agent in a content creation pipeline.

Your role:
1. Analyze the given topic and identify 5-8 key subtopics
2. Provide factual information, statistics, and expert quotes for each
3. Identify trending angles and unique perspectives
4. Flag any controversial claims that need verification
5. Suggest primary and secondary sources

Output format (JSON):
{
    "topic": "...",
    "key_subtopics": [
        {"title": "...", "key_facts": [...], "statistics": [...], "expert_quotes": [...]}
    ],
    "trending_angles": [...],
    "controversial_claims": [...],
    "suggested_sources": [...],
    "unique_angle": "..."
}

Be thorough but concise. Prioritize recent (2024-2026) data."""

    async def execute(self, topic: str = "", **kwargs) -> AgentResult:
        """Research a given topic and return structured findings."""
        prompt = f"""Research the following topic thoroughly:

Topic: {topic}

Provide:
1. 5-8 key subtopics with supporting facts and statistics
2. Expert perspectives and notable quotes
3. Current trends and unique angles
4. Any controversial claims that need fact-checking
5. A suggested unique angle for the article

Return as structured JSON."""

        response = await self._call_mimo(prompt)

        return AgentResult(
            agent_name=self.name,
            content=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            reasoning=response.reasoning_content,
            metadata={
                "topic": topic,
                "has_statistics": "statistics" in response.content.lower(),
                "has_quotes": "quote" in response.content.lower(),
                "output_length": len(response.content),
            },
        )
