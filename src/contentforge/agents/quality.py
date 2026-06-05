"""Quality Agent — Fact-checking and quality assurance."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class QualityAgent(BaseAgent):
    name = "quality"
    description = "Fact-checks content, scores quality, and flags issues"

    system_prompt = """You are the Quality Agent in a content creation pipeline.

Your role:
1. Score overall content quality (0-100)
2. Check factual accuracy of claims and statistics
3. Verify logical consistency throughout the piece
4. Detect potential plagiarism patterns
5. Check for bias or unbalanced perspectives
6. Verify all statistics have proper context
7. Ensure the content delivers on the title's promise
8. Check readability metrics

Quality dimensions (score each 0-100):
- Accuracy: Factual correctness
- Completeness: Covers the topic thoroughly
- Clarity: Easy to understand
- Engagement: Keeps reader interest
- Originality: Unique perspective
- Structure: Logical organization
- SEO: Search optimization
- Readability: Appropriate reading level

Output format (JSON):
{
    "overall_score": N,
    "pass_threshold": true|false,
    "dimensions": {
        "accuracy": {"score": N, "notes": "..."},
        "completeness": {"score": N, "notes": "..."},
        "clarity": {"score": N, "notes": "..."},
        "engagement": {"score": N, "notes": "..."},
        "originality": {"score": N, "notes": "..."},
        "structure": {"score": N, "notes": "..."},
        "seo": {"score": N, "notes": "..."},
        "readability": {"score": N, "notes": "..."}
    },
    "factual_issues": [...],
    "logical_inconsistencies": [...],
    "bias_flags": [...],
    "improvement_suggestions": [...],
    "strengths": [...]
}"""

    async def execute(
        self,
        content: str = "",
        threshold: float = 0.8,
        title: str = "",
        **kwargs,
    ) -> AgentResult:
        """Score content quality and flag issues."""
        prompt = f"""Evaluate the quality of the following article.

Title: {title}
Quality threshold: {threshold * 100}%

CONTENT:
{content}

Score each dimension (0-100) and provide:
1. Overall quality score
2. Per-dimension scores with notes
3. Factual issues found
4. Logical inconsistencies
5. Bias flags
6. Improvement suggestions
7. Key strengths

Return as structured JSON."""

        response = await self._call_mimo(prompt)

        # Parse score from response for metadata
        overall_score = 0
        try:
            import json

            parsed = json.loads(response.content)
            overall_score = parsed.get("overall_score", 0)
        except (json.JSONDecodeError, AttributeError):
            pass

        return AgentResult(
            agent_name=self.name,
            content=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            reasoning=response.reasoning_content,
            metadata={
                "overall_score": overall_score,
                "threshold": threshold,
                "passes_threshold": overall_score >= threshold * 100,
                "content_length": len(content),
            },
        )
