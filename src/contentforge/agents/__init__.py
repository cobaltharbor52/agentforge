"""ContentForge Agents — 8 specialized AI agents for content pipeline."""

from .base import BaseAgent, AgentResult
from .research import ResearchAgent
from .outline import OutlineAgent
from .writer import WriterAgent
from .seo import SEOAgent
from .editor import EditorAgent
from .translator import TranslatorAgent
from .quality import QualityAgent
from .publisher import PublisherAgent

AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "research": ResearchAgent,
    "outline": OutlineAgent,
    "writer": WriterAgent,
    "seo": SEOAgent,
    "editor": EditorAgent,
    "translator": TranslatorAgent,
    "quality": QualityAgent,
    "publisher": PublisherAgent,
}


def get_agent(name: str, **kwargs) -> BaseAgent:
    cls = AGENT_REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Unknown agent: {name}. Available: {list(AGENT_REGISTRY)}")
    return cls(**kwargs)


__all__ = [
    "BaseAgent",
    "AgentResult",
    "AGENT_REGISTRY",
    "get_agent",
    "ResearchAgent",
    "OutlineAgent",
    "WriterAgent",
    "SEOAgent",
    "EditorAgent",
    "TranslatorAgent",
    "QualityAgent",
    "PublisherAgent",
]
