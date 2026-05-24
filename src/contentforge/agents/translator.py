"""Translator Agent — Multi-language content adaptation."""

from __future__ import annotations

from .base import BaseAgent, AgentResult


class TranslatorAgent(BaseAgent):
    name = "translator"
    description = "Adapts content to target languages while preserving tone and SEO"

    system_prompt = """You are the Translator Agent in a content creation pipeline.

Your role:
1. Translate content to the target language accurately
2. Adapt cultural references and idioms for the target audience
3. Preserve SEO keywords (transliterate or localize as appropriate)
4. Maintain heading structure and Markdown formatting
5. Keep proper nouns and brand names unchanged unless localized versions exist
6. Adapt statistics and date formats for the target locale
7. Preserve the original tone and voice

Supported languages:
- zh (Chinese Simplified) — 优先使用简体中文
- ms (Malay) — Gunakan bahasa Melayu standard
- ja (Japanese) — 日本語で自然な表現を使用
- ko (Korean) — 한국어로 자연스러운 표현 사용
- id (Indonesian) — Gunakan bahasa Indonesia baku
- th (Thai) — ใช้ภาษาไทยที่เป็นธรรมชาติ
- vi (Vietnamese) — Sử dụng tiếng Việt tự nhiên
- ar (Arabic) — استخدم اللغة العربية الفصحى

Output: Full translated article in Markdown, same structure as original."""

    async def execute(
        self,
        content: str = "",
        target_language: str = "zh",
        source_language: str = "en",
        preserve_keywords: list[str] | None = None,
        **kwargs,
    ) -> AgentResult:
        """Translate content to target language."""
        keywords_note = ""
        if preserve_keywords:
            keywords_note = (
                f"\nPreserve these keywords in original form: "
                f"{', '.join(preserve_keywords)}"
            )

        prompt = f"""Translate the following article from {source_language} to {target_language}.

Rules:
- Maintain Markdown formatting exactly
- Adapt cultural references naturally
- Keep brand names and proper nouns unchanged{keywords_note}

ARTICLE:
{content}

Return the full translated article in Markdown."""

        response = await self._call_mimo(prompt, max_tokens=8192)

        return AgentResult(
            agent_name=self.name,
            content=response.content,
            tokens_used=response.usage.total_tokens,
            latency_ms=response.latency_ms,
            metadata={
                "source_language": source_language,
                "target_language": target_language,
                "input_length": len(content),
                "output_length": len(response.content),
            },
        )
