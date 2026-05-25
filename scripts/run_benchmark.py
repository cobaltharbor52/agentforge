#!/usr/bin/env python3
"""Benchmark: measure token consumption across multiple pipeline runs."""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from contentforge.core.config import ContentForgeConfig
from contentforge.pipeline.orchestrator import PipelineOrchestrator

TOPICS = [
    "Machine Learning in Production",
    "The Future of Remote Work",
    "Cybersecurity Trends 2026",
    "Sustainable Technology Solutions",
    "AI-Powered Education Tools",
]


async def run_benchmark(num_runs: int = 3):
    config = ContentForgeConfig.from_env()
    config.pipeline.target_word_count = 1000  # Shorter for benchmark

    results = []

    for i in range(min(num_runs, len(TOPICS))):
        topic = TOPICS[i]
        print(f"\n{'='*60}")
        print(f"Run {i+1}/{num_runs}: {topic}")
        print("=" * 60)

        orchestrator = PipelineOrchestrator(config)
        result = await orchestrator.run(topic)

        if result.ok:
            summary = result.summary()
            results.append(summary)
            print(f"  Words: {summary['word_count']}")
            print(f"  Tokens: {summary['total_tokens']:,}")
            print(f"  Duration: {summary['pipeline_duration_s']:.1f}s")
        else:
            print(f"  FAILED: {result.status}")

    # Aggregate
    if results:
        total_tokens = sum(r["total_tokens"] for r in results)
        avg_tokens = total_tokens / len(results)
        avg_duration = sum(r["pipeline_duration_s"] for r in results) / len(results)

        print(f"\n{'='*60}")
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"  Runs: {len(results)}")
        print(f"  Total tokens: {total_tokens:,}")
        print(f"  Avg tokens/run: {avg_tokens:,.0f}")
        print(f"  Avg duration: {avg_duration:.1f}s")
        print(f"  Est. daily (50 runs): {avg_tokens * 50:,.0f} tokens")
        print("=" * 60)

        # Save results
        output = Path("benchmark_results.json")
        output.write_text(json.dumps({
            "runs": results,
            "aggregate": {
                "total_tokens": total_tokens,
                "avg_tokens": avg_tokens,
                "avg_duration": avg_duration,
            },
        }, indent=2))
        print(f"\nResults saved to {output}")


if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    asyncio.run(run_benchmark(runs))
