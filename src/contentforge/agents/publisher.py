"""Publisher Agent — Formats and exports content for various platforms."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .base import BaseAgent, AgentResult


class PublisherAgent(BaseAgent):
    name = "publisher"
    description = "Formats content for target platforms and exports files"

    system_prompt = """You are the Publisher Agent in a content creation pipeline.

Your role:
1. Format content for the target platform(s)
2. Generate platform-specific metadata
3. Create social media snippets for distribution
4. Generate email newsletter version
5. Create plain-text fallback version
6. Add proper front matter (YAML/TOML as needed)

Platform formats:
- markdown: Clean Markdown with YAML front matter
- html: Semantic HTML5 with proper meta tags
- wordpress: WordPress-compatible with shortcodes
- medium: Medium-optimized (clean, no front matter)
- newsletter: Email-friendly HTML with inline styles
- social: Social media snippets (Twitter, LinkedIn, Facebook)

Output format (JSON):
{
    "formats": {
        "markdown": "...",
        "html_snippet": "...",
        "social_twitter": "...",
        "social_linkedin": "...",
        "newsletter_subject": "...",
        "newsletter_preview": "..."
    },
    "metadata": {
        "title": "...",
        "description": "...",
        "tags": [...],
        "category": "...",
        "reading_time": "...",
        "word_count": N
    }
}"""

    async def execute(
        self,
        content: str = "",
        title: str = "",
        publish_targets: list[str] | None = None,
        output_dir: str = "./output",
        **kwargs,
    ) -> AgentResult:
        """Format and export content for target platforms."""
        targets = publish_targets or ["markdown"]
        targets_str = ", ".join(targets)

        prompt = f"""Format the following article for these platforms: {targets_str}

Title: {title}

CONTENT:
{content}

Generate:
1. Platform-specific formatted versions
2. Social media snippets (Twitter: 280 chars, LinkedIn: professional tone)
3. Email newsletter subject line and preview text
4. Complete metadata (tags, category, reading time, word count)

Return as structured JSON."""

        response = await self._call_mimo(prompt)

        # Write output files
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        # Save the main content
        content_file = output_path / f"{timestamp}_article.md"
        content_file.write_text(content)

        # Save publisher output (social snippets, metadata)
        publisher_file = output_path / f"{timestamp}_publisher.json"
        publisher_file.write_text(response.content)

        return AgentResult(
            agent_name=self.name,
            content=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            metadata={
                "publish_targets": targets,
                "output_files": [str(content_file), str(publisher_file)],
                "content_length": len(content),
            },
        )
