"""Writer Agent — Generates the actual content draft."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class WriterAgent(BaseAgent):
    name = "writer"
    description = "Generates full content draft from outline and research"

    system_prompt = """You are the Writer Agent in a content creation pipeline.

Your role:
1. Write engaging, well-researched content following the provided outline
2. Maintain consistent tone and voice throughout
3. Include natural keyword integration (not keyword stuffing)
4. Use varied sentence structures and paragraph lengths
5. Add relevant examples, analogies, and data points
6. Write in a style that's informative yet accessible

Writing guidelines:
- Start with a compelling hook
- Use subheadings (##) for each major section
- Include bullet points and numbered lists for scannability
- Add internal transition sentences between sections
- End with a strong conclusion and call-to-action
- Write in active voice predominantly
- Cite statistics with source context (not raw URLs)

Output: Full article in Markdown format."""

    async def execute(
        self,
        outline: str = "",
        research_data: str = "",
        language: str = "en",
        **kwargs,
    ) -> AgentResult:
        """Generate a full content draft."""
        prompt = f"""Write a complete article based on the following outline and research.

Language: {language}

OUTLINE:
{outline}

RESEARCH DATA:
{research_data}

Write the full article in Markdown. Follow the outline structure precisely.
Each section should meet its word allocation target.
Include natural keyword integration as specified in the outline."""

        response = await self._call_mimo(prompt, max_tokens=8192)

        word_count = len(response.content.split())

        return AgentResult(
            agent_name=self.name,
            content=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            reasoning=response.reasoning_content,
            metadata={
                "word_count": word_count,
                "language": language,
                "output_length": len(response.content),
            },
        )
