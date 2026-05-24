"""Editor Agent — Refines and polishes content quality."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class EditorAgent(BaseAgent):
    name = "editor"
    description = "Refines content for clarity, grammar, tone, and readability"

    system_prompt = """You are the Editor Agent in a content creation pipeline.

Your role:
1. Fix grammar, spelling, and punctuation errors
2. Improve sentence clarity and readability
3. Ensure consistent tone and voice
4. Remove redundancy and filler words
5. Strengthen weak transitions
6. Verify factual claims have proper attribution
7. Improve paragraph flow and pacing
8. Ensure the content matches the target reading level

Editing principles:
- Preserve the author's voice while improving clarity
- Short sentences for impact, longer for explanation
- Every paragraph must earn its place
- Active voice over passive
- Specific over vague
- Show, don't tell

Output: Return the FULL edited article in Markdown, plus a change summary."""

    async def execute(
        self,
        content: str = "",
        seo_recommendations: str = "",
        target_reading_level: str = "general",
        **kwargs,
    ) -> AgentResult:
        """Edit and refine the content draft."""
        seo_block = ""
        if seo_recommendations:
            seo_block = f"SEO RECOMMENDATIONS TO INCORPORATE:\n{seo_recommendations}\n"

        prompt = f"""Edit the following article for maximum quality.

Target reading level: {target_reading_level}

{seo_block}
CONTENT:
{content}

Return:
1. The FULL edited article in Markdown (not a diff)
2. A brief change summary at the end (as a comment block)"""

        response = await self._call_mimo(prompt, max_tokens=8192)

        return AgentResult(
            agent_name=self.name,
            content=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            reasoning=response.reasoning_content,
            metadata={
                "input_length": len(content),
                "output_length": len(response.content),
                "reading_level": target_reading_level,
            },
        )
