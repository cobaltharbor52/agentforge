#!/usr/bin/env python3
"""Custom pipeline: use individual agents instead of full pipeline."""

import asyncio
from contentforge.core.config import ContentForgeConfig
from contentforge.core.mimo_client import MiMoClient
from contentforge.core.token_tracker import TokenTracker
from contentforge.agents.research import ResearchAgent
from contentforge.agents.writer import WriterAgent
from contentforge.agents.quality import QualityAgent


async def main():
    config = ContentForgeConfig.from_env()
    tracker = TokenTracker()

    async with MiMoClient(config.mimo) as client:
        # Step 1: Research
        research = ResearchAgent(config=config, client=client, tracker=tracker)
        research_result = await research.run(topic="Quantum Computing in 2026")
        print(f"Research: {research_result.tokens_used} tokens")

        # Step 2: Write directly (skip outline for speed)
        writer = WriterAgent(config=config, client=client, tracker=tracker)
        writer_result = await writer.run(
            outline="1. Intro 2. Current State 3. Applications 4. Future",
            research_data=research_result.content,
        )
        print(f"Writer: {writer_result.tokens_used} tokens")

        # Step 3: Quality check
        quality = QualityAgent(config=config, client=client, tracker=tracker)
        quality_result = await quality.run(
            content=writer_result.content, threshold=0.7
        )
        print(f"Quality: {quality_result.tokens_used} tokens")
        print(f"Score: {quality_result.metadata.get('overall_score', 'N/A')}")

    # Report
    print(f"\nTotal: {tracker.total_tokens:,} tokens")
    print(tracker.report())


if __name__ == "__main__":
    asyncio.run(main())
