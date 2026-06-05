"""Token consumption tracking and reporting across all agents."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AgentMetrics:
    """Per-agent token and performance metrics."""

    agent_name: str
    call_count: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0
    total_latency_ms: float = 0.0
    errors: int = 0
    retries: int = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.total_latency_ms / self.call_count

    @property
    def tokens_per_call(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.total_tokens / self.call_count

    @property
    def cache_hit_rate(self) -> float:
        if self.prompt_tokens == 0:
            return 0.0
        return self.cached_tokens / self.prompt_tokens

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_name,
            "calls": self.call_count,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cached_tokens": self.cached_tokens,
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "tokens_per_call": round(self.tokens_per_call, 0),
            "cache_hit_rate": f"{self.cache_hit_rate:.1%}",
            "errors": self.errors,
            "retries": self.retries,
        }


class TokenTracker:
    """Global token consumption tracker for the pipeline.

    Tracks per-agent and aggregate metrics. Persists to JSON for
    daily/weekly/monthly consumption analysis.
    """

    def __init__(self, output_dir: str = "./output"):
        self._agents: dict[str, AgentMetrics] = {}
        self._pipeline_start: Optional[float] = None
        self._pipeline_end: Optional[float] = None
        self._output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
        self._run_id = time.strftime("%Y%m%d_%H%M%S")

    def start_pipeline(self) -> None:
        self._pipeline_start = time.monotonic()

    def end_pipeline(self) -> None:
        self._pipeline_end = time.monotonic()

    def record(
        self,
        agent_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cached_tokens: int = 0,
        errors: int = 0,
        retries: int = 0,
    ) -> None:
        if agent_name not in self._agents:
            self._agents[agent_name] = AgentMetrics(agent_name=agent_name)

        m = self._agents[agent_name]
        m.call_count += 1
        m.prompt_tokens += prompt_tokens
        m.completion_tokens += completion_tokens
        m.total_tokens += prompt_tokens + completion_tokens
        m.cached_tokens += cached_tokens
        m.total_latency_ms += latency_ms
        m.errors += errors
        m.retries += retries

    @property
    def total_tokens(self) -> int:
        return sum(m.total_tokens for m in self._agents.values())

    @property
    def total_calls(self) -> int:
        return sum(m.call_count for m in self._agents.values())

    @property
    def pipeline_duration_s(self) -> float:
        if not self._pipeline_start:
            return 0.0
        end = self._pipeline_end or time.monotonic()
        return end - self._pipeline_start

    def summary(self) -> dict:
        return {
            "run_id": self._run_id,
            "pipeline_duration_s": round(self.pipeline_duration_s, 2),
            "total_tokens": self.total_tokens,
            "total_calls": self.total_calls,
            "agents": {name: m.to_dict() for name, m in self._agents.items()},
        }

    def report(self) -> str:
        """Human-readable token consumption report."""
        lines = [
            "=" * 60,
            "  ContentForge Token Consumption Report",
            f"  Run: {self._run_id}",
            "=" * 60,
            "",
        ]

        total_prompt = sum(m.prompt_tokens for m in self._agents.values())
        total_comp = sum(m.completion_tokens for m in self._agents.values())
        total_cached = sum(m.cached_tokens for m in self._agents.values())

        lines.append(f"  Pipeline Duration: {self.pipeline_duration_s:.1f}s")
        lines.append(f"  Total Tokens: {self.total_tokens:,}")
        lines.append(f"    Prompt: {total_prompt:,} | Completion: {total_comp:,}")
        lines.append(f"    Cache Hit: {total_cached:,} ({total_cached / max(total_prompt, 1):.1%})")
        lines.append(f"  Total API Calls: {self.total_calls}")
        lines.append("")

        lines.append(
            f"  {'Agent':<20} {'Calls':>6} {'Tokens':>10} {'Avg/call':>10} {'Latency':>10}"
        )
        lines.append("  " + "-" * 58)

        for name, m in sorted(self._agents.items(), key=lambda x: -x[1].total_tokens):
            lines.append(
                f"  {name:<20} {m.call_count:>6} {m.total_tokens:>10,} "
                f"{m.tokens_per_call:>10,.0f} {m.avg_latency_ms:>9.0f}ms"
            )

        lines.append("  " + "-" * 58)
        lines.append(
            f"  {'TOTAL':<20} {self.total_calls:>6} {self.total_tokens:>10,} {'':>10} {'':>10}"
        )
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def save(self, path: Optional[str] = None) -> Path:
        """Persist metrics to JSON."""
        out = Path(path) if path else Path(self._output_dir) / "metrics" / f"{self._run_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            json.dump(self.summary(), f, indent=2)
        return out
