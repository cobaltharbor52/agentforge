"""Text processing utilities."""

from __future__ import annotations

import re


def word_count(text: str) -> int:
    """Count words in text (handles both English and CJK)."""
    # Count CJK characters as individual words
    cjk = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", text))
    # Count English words
    english_words = len(re.findall(r"[a-zA-Z]+", text))
    return cjk + english_words


def extract_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML front matter from Markdown."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            import yaml

            fm = yaml.safe_load(parts[1]) or {}
            return fm, parts[2].strip()
    return {}, text


def truncate(text: str, max_chars: int = 100, suffix: str = "...") -> str:
    """Truncate text to max characters with suffix."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def reading_time(text: str, wpm: int = 200) -> str:
    """Estimate reading time."""
    words = word_count(text)
    minutes = max(1, round(words / wpm))
    return f"{minutes} min read"
