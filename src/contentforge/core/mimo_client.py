"""Backward-compatibility shim.

The implementation moved to :mod:`contentforge.core.llm_client` when ContentForge
became provider-agnostic. This module re-exports the public names so existing
imports (``from contentforge.core.mimo_client import MiMoClient``) keep working.
Prefer importing from ``contentforge.core.llm_client`` in new code.
"""

from __future__ import annotations

from .llm_client import (  # noqa: F401
    ChatMessage,
    ChatResponse,
    LLMClient,
    MiMoClient,
    StreamChunk,
    TokenUsage,
)

__all__ = [
    "ChatMessage",
    "ChatResponse",
    "LLMClient",
    "MiMoClient",
    "StreamChunk",
    "TokenUsage",
]
