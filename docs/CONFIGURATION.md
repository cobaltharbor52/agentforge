# Configuration Reference

## YAML Config

```yaml
providers:
  default: openai
  openai:
    model: gpt-4o
    api_key: ${OPENAI_API_KEY}

agents:
  - name: researcher
    model: openai
    temperature: 0.7
```

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | API key |
| `CONTENTFORGE_CONFIG` | Path to YAML config |
