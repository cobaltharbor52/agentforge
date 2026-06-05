"""
ContentForge — 8-Agent AI Content Pipeline.

Provider-agnostic: runs on any OpenAI-compatible /chat/completions endpoint
(OpenAI, OpenRouter, Ollama, llama.cpp, Xiaomi MiMo, ...).

Usage:
    contentforge generate "AI in Healthcare" --words 2000 --output ./output
    contentforge generate "AI Ethics" --translate zh --translate ms
    contentforge agents
"""

__version__ = "1.0.0"
__author__ = "ContentForge Team"
