"""Tests for configuration schema validation."""

import pytest
from agentforge.config import Config, ValidationError


def test_valid_config():
    cfg = Config(model="gpt-4o", agents=["researcher", "writer"])
    assert cfg.model == "gpt-4o"


def test_empty_agents_raises():
    with pytest.raises(ValidationError, match="at least one agent"):
        Config(model="gpt-4o", agents=[])


def test_invalid_model_raises():
    with pytest.raises(ValidationError, match="unsupported model"):
        Config(model="invalid-model", agents=["researcher"])
