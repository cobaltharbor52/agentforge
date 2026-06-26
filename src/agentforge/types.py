"""Type definitions for pipeline results."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AgentResult:
    name: str
    output: str
    tokens_used: int
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PipelineResult:
    final_output: str
    agent_results: list[AgentResult]
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None
