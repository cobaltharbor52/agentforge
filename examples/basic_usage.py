#!/usr/bin/env python3
"""Basic ContentForge usage example."""

import asyncio
from contentforge.core.config import ContentForgeConfig
from contentforge.pipeline.orchestrator import PipelineOrchestrator


async def main():
    # Load config from environment (MIMO_API_KEY must be set)
    config = ContentForgeConfig.from_env()
    config.pipeline.target_word_count = 1500

    # Create orchestrator and run
    orchestrator = PipelineOrchestrator(config)
    result = await orchestrator.run("The Rise of AI Agents in 2026")

    if result.ok:
        print(f"Article generated: {len(result.article.split())} words")
        print(f"Total tokens: {result.total_tokens:,}")
        print(f"Duration: {result.pipeline_duration_s:.1f}s")
        print(f"Metrics saved: {result.metrics_path}")
        print("\n--- Article Preview ---")
        print(result.article[:500] + "...")
    else:
        print(f"Pipeline failed: {result.status}")


if __name__ == "__main__":
    asyncio.run(main())
