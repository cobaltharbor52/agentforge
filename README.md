# ContentForge

> **8-Agent AI Content Pipeline for any OpenAI-compatible LLM**
>
> From topic to published article in minutes — research, write, optimize, translate, and publish with 8 specialized AI agents orchestrated through a single pipeline.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 112](https://img.shields.io/badge/tests-112-brightgreen.svg)](tests/)
[![LOC: 2,900+](https://img.shields.io/badge/LOC-2%2C900%2B-orange.svg)](src/)

Works with **OpenAI, OpenRouter, Ollama, llama.cpp, Xiaomi MiMo**, or any endpoint that speaks the OpenAI `/chat/completions` protocol. Pick a provider with one config line — no code changes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ContentForge Pipeline                       │
│              Any OpenAI-compatible LLM backend                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ 1.Research│──▶│2.Outline │──▶│ 3.Writer │──▶│  4.SEO   │    │
│  │  Agent   │   │  Agent   │   │  Agent   │   │  Agent   │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│                                                     │          │
│                                                     ▼          │
│  ┌──────────┐   ┌──────────┐        ┌──────────────────┐       │
│  │8.Publisher│◀──│7.Translate│◀───────│ 5.Editor ──▶ 6.Quality │
│  │  Agent   │   │  Agent   │        │  (iterate if < threshold)│
│  └──────────┘   └──────────┘        └──────────────────┘       │
│       │                                                        │
│       ▼                                                        │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Token Tracker & Metrics                  │      │
│  │  Per-agent consumption · Cache hit rate · Latency    │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  Protocol: OpenAI-compatible /chat/completions                 │
│  Auth: bearer token or api-key header (per provider)           │
│  Streaming SSE · optional reasoning_content support            │
└─────────────────────────────────────────────────────────────────┘
```

## 8 Specialized Agents

| # | Agent | Role | Avg Tokens/Call |
|---|-------|------|-----------------|
| 1 | **Research** | Gathers facts, statistics, expert quotes | ~800 |
| 2 | **Outline** | Structures content with word allocation | ~600 |
| 3 | **Writer** | Generates full article draft | ~2,000 |
| 4 | **SEO** | Analyzes keyword density, meta tags, CTR | ~1,000 |
| 5 | **Editor** | Refines clarity, grammar, tone | ~2,000 |
| 6 | **Quality** | Fact-checks, scores 8 quality dimensions | ~1,000 |
| 7 | **Translator** | Multi-language adaptation (zh/ms/ja/ko/id/th/vi/ar) | ~1,200 |
| 8 | **Publisher** | Formats for markdown/HTML/WordPress/social | ~800 |

**Total per pipeline run: ~9,400 tokens** (single language)

## Supported Providers

ContentForge talks to any OpenAI-compatible `/chat/completions` endpoint. Built-in presets:

| Provider | `provider=` | Default model | Auth | Env vars |
|----------|-------------|---------------|------|----------|
| OpenAI | `openai` | `gpt-4o-mini` | Bearer | `OPENAI_API_KEY`, `OPENAI_BASE_URL` |
| OpenRouter | `openrouter` | `openai/gpt-4o-mini` | Bearer | `OPENROUTER_API_KEY` |
| Ollama (local) | `ollama` | `llama3.1` | Bearer | `OLLAMA_BASE_URL` |
| Xiaomi MiMo | `mimo` | `mimo-v2.5-pro` | api-key | `MIMO_API_KEY` |

Point `base_url` at any other compatible endpoint (llama.cpp, vLLM, LM Studio, a local proxy) and it just works. The pipeline benefits from models that expose a `reasoning_content` field (used by the Quality Agent's 8-dimension scoring) and strong multilingual output (used by the Translator Agent), but neither is required.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Pick any provider — set its API key (OpenAI shown here)
export OPENAI_API_KEY="sk-..."

# Generate content (uses the default provider unless overridden in config)
contentforge generate "AI in Healthcare" --words 2000 --output ./output

# With translation
contentforge generate "AI Ethics" --translate zh --translate ms

# View token consumption
contentforge report output/metrics/*.json

# List agents
contentforge agents
```

## Usage as Library

```python
import asyncio
from contentforge.core.config import ContentForgeConfig
from contentforge.pipeline.orchestrator import PipelineOrchestrator

async def main():
    config = ContentForgeConfig.from_env()
    config.pipeline.target_word_count = 3000
    config.pipeline.enable_translation = True
    config.pipeline.target_languages = ["zh", "ms"]

    orchestrator = PipelineOrchestrator(config)
    result = await orchestrator.run("The Future of AI Agents")

    print(f"Article: {len(result.article.split())} words")
    print(f"Tokens: {result.total_tokens:,}")
    print(f"Duration: {result.pipeline_duration_s:.1f}s")
    print(f"Translations: {list(result.translations.keys())}")

    # Token consumption report
    print(orchestrator.tracker.report())

asyncio.run(main())
```

## Token Consumption

Average pipeline run consumes **~9,400 tokens** across 8 agents:

```
============================================================
  ContentForge Token Consumption Report
  Run: 20260526_143022
============================================================

  Pipeline Duration: 12.3s
  Total Tokens: 9,420
    Prompt: 4,800 | Completion: 4,620
    Cache Hit: 1,200 (25.0%)
  Total API Calls: 8

  Agent                Calls     Tokens    Avg/call   Latency
  ----------------------------------------------------------
  writer                    1      2,100      2,100     2500ms
  editor                    1      2,050      2,050     2200ms
  translator                1      1,200      1,200     1800ms
  quality                   1      1,000      1,000     1500ms
  seo                       1        980        980     1200ms
  research                  1        820        820     1100ms
  publisher                 1        780        780      900ms
  outline                   1        590        590      800ms
  ----------------------------------------------------------
  TOTAL                     8      9,520
============================================================
```

Daily estimate: **50-100 pipeline runs** = ~500K–1M tokens/day

## Configuration

```yaml
# contentforge.yaml
llm:
  provider: openai          # openai | openrouter | ollama | mimo
  api_key: ${OPENAI_API_KEY}
  # base_url and model default from the provider preset; override if needed
  # base_url: https://api.openai.com/v1
  # model: gpt-4o-mini
  max_tokens: 4096
  temperature: 0.7
  max_retries: 3

pipeline:
  target_word_count: 2000
  language: en
  seo_enabled: true
  quality_threshold: 0.8
  max_iterations: 3
  enable_translation: false
  target_languages: [zh, ms]
  publish_targets: [markdown, html]

agents:
  - name: writer
    temperature_override: 0.8
    max_tokens_override: 8192
  - name: quality
    system_prompt_override: "Custom quality rules..."
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=contentforge --cov-report=term-missing

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Verbose output
pytest -v
```

**112 tests** covering:
- Configuration management (17 tests)
- Multi-backend LLM config: presets, auth styles, env resolution (16 tests)
- Token tracking & reporting (14 tests)
- Text utilities (12 tests)
- Export utilities (4 tests)
- Agent base class & all 8 agents (34 tests)
- Pipeline orchestration (8 tests)
- Error handling & edge cases (7 tests)

## Project Structure

```
contentforge/
├── src/contentforge/
│   ├── __init__.py
│   ├── cli.py                    # Click CLI with Rich output
│   ├── agents/
│   │   ├── __init__.py           # Agent registry
│   │   ├── base.py               # BaseAgent abstract class
│   │   ├── research.py           # Agent 1: Research
│   │   ├── outline.py            # Agent 2: Outline
│   │   ├── writer.py             # Agent 3: Writer
│   │   ├── seo.py                # Agent 4: SEO
│   │   ├── editor.py             # Agent 5: Editor
│   │   ├── translator.py         # Agent 6: Translator
│   │   ├── quality.py            # Agent 7: Quality
│   │   └── publisher.py          # Agent 8: Publisher
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Pydantic config (multi-provider presets)
│   │   ├── llm_client.py         # OpenAI-compatible client (SSE streaming)
│   │   ├── mimo_client.py        # Backward-compat shim → llm_client
│   │   └── token_tracker.py      # Per-agent token metrics
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── orchestrator.py       # 8-agent pipeline coordinator
│   └── utils/
│       ├── __init__.py
│       ├── text.py               # Word count, slugify, reading time
│       └── export.py             # Markdown/HTML export
├── tests/
│   ├── conftest.py               # Shared fixtures
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_token_tracker.py
│   │   ├── test_utils.py
│   │   └── test_agents.py
│   └── integration/
│       └── test_pipeline.py
├── docs/
│   └── api-reference.md
├── examples/
│   ├── basic_usage.py
│   └── custom_pipeline.py
├── scripts/
│   └── run_benchmark.py
├── pyproject.toml
├── LICENSE
└── README.md
```

## API Reference

### LLMClient

```python
from contentforge.core.llm_client import LLMClient, ChatMessage

async with LLMClient(config) as client:
    # Non-streaming
    response = await client.chat([
        ChatMessage(role="system", content="You are helpful."),
        ChatMessage(role="user", content="Explain AI agents."),
    ])
    print(response.content)
    print(f"Tokens: {response.usage.total_tokens}")

    # Streaming
    async for chunk in client.stream_chunks(messages):
        print(chunk.delta, end="", flush=True)
```

**Auth styles**: `provider="openai"` (and openrouter/ollama) use `Authorization: Bearer`; `provider="mimo"` uses the `api-key` header. The right style is selected automatically from the provider preset. `MiMoClient` remains importable as a backward-compatible alias of `LLMClient`.

### TokenTracker

```python
from contentforge.core.token_tracker import TokenTracker

tracker = TokenTracker()
tracker.start_pipeline()
# ... run agents ...
tracker.end_pipeline()

print(tracker.report())  # Human-readable report
tracker.save()           # Persist to JSON
```

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Provider-agnostic** — works with OpenAI, OpenRouter, Ollama, llama.cpp, Xiaomi MiMo, or any OpenAI-compatible `/chat/completions` endpoint.
