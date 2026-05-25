# API Reference

## Core Modules

### `contentforge.core.config`

Configuration management using Pydantic models.

#### `MiMoConfig`

```python
MiMoConfig(
    api_key: str,           # Token Plan API key
    base_url: str,          # Default: https://token-plan-sgp.xiaomimimo.com/v1
    model: str,             # Default: mimo-v2.5-pro
    max_tokens: int,        # Default: 4096
    temperature: float,     # Default: 0.7
    top_p: float,           # Default: 0.9
    timeout: int,           # Default: 120s
    max_retries: int,       # Default: 3
)
```

**Important**: Uses `api-key` header, NOT `Authorization: Bearer`.

### `contentforge.core.mimo_client`

#### `MiMoClient`

Async context manager for MiMo API calls.

```python
async with MiMoClient(config) as client:
    response = await client.chat(messages)
    async for chunk in client.stream_chunks(messages):
        print(chunk.delta)
```

#### `ChatMessage`

```python
ChatMessage(role: str, content: str, reasoning_content: Optional[str] = None)
```

#### `ChatResponse`

```python
ChatResponse(
    content: str,
    reasoning_content: Optional[str],
    usage: TokenUsage,
    model: str,
    finish_reason: str,
    latency_ms: float,
)
```

#### `TokenUsage`

```python
TokenUsage(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cached_tokens: int,
)
```

### `contentforge.core.token_tracker`

#### `TokenTracker`

```python
tracker = TokenTracker(output_dir="./output")
tracker.start_pipeline()
tracker.record("agent_name", prompt_tokens=100, completion_tokens=50, latency_ms=200)
tracker.end_pipeline()
print(tracker.report())
tracker.save()
```

## Agents

### `BaseAgent`

Abstract base class. All agents implement:

```python
async def execute(**kwargs) -> AgentResult
async def run(**kwargs) -> AgentResult  # wraps execute with error handling
```

### `AgentResult`

```python
AgentResult(
    agent_name: str,
    status: str,          # "success" | "partial" | "failed"
    content: str,
    metadata: dict,
    tokens_used: int,
    latency_ms: float,
    error: Optional[str],
    reasoning: Optional[str],
)
```

### Agent-Specific Parameters

| Agent | `execute()` params |
|-------|-------------------|
| Research | `topic: str` |
| Outline | `research_data: str, target_words: int` |
| Writer | `outline: str, research_data: str, language: str` |
| SEO | `content: str, target_keywords: list[str]` |
| Editor | `content: str, seo_recommendations: str, target_reading_level: str` |
| Translator | `content: str, target_language: str, source_language: str, preserve_keywords: list[str]` |
| Quality | `content: str, threshold: float, title: str` |
| Publisher | `content: str, title: str, publish_targets: list[str], output_dir: str` |

## Pipeline

### `PipelineOrchestrator`

```python
orchestrator = PipelineOrchestrator(config)
result = await orchestrator.run(topic="Your Topic")
```

### `PipelineResult`

```python
PipelineResult(
    status: str,
    article: str,
    research: str,
    outline: str,
    seo_analysis: str,
    quality_report: str,
    publisher_output: str,
    translations: dict[str, str],
    agent_results: dict[str, AgentResult],
    metrics_path: str,
    total_tokens: int,
    pipeline_duration_s: float,
)
```
