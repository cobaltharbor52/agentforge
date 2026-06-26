# Architecture

## Overview

```
[Input] -> [Researcher Agent] -> [Writer Agent] -> [Editor Agent] -> [SEO Agent] -> [Fact-Check Agent] -> [Output]
```

## Agent Pipeline

Each agent runs asynchronously using `asyncio.gather` where independent.
Dependencies are resolved via a DAG.

## Token Tracking

Every API call is logged with:
- Input tokens
- Output tokens
- Cost (USD)
- Latency (ms)

## Provider Abstraction

All LLM calls go through a unified interface:
```python
class LLMProvider(ABC):
    async def complete(self, messages: list[dict]) -> str: ...
```
