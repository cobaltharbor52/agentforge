"""Unit tests for token tracking and reporting."""

import json
import os
import pytest
import tempfile

from contentforge.core.token_tracker import AgentMetrics, TokenTracker


class TestAgentMetrics:
    def test_initial_state(self):
        m = AgentMetrics(agent_name="test")
        assert m.call_count == 0
        assert m.total_tokens == 0
        assert m.avg_latency_ms == 0.0
        assert m.tokens_per_call == 0.0
        assert m.cache_hit_rate == 0.0

    def test_record_single_call(self):
        m = AgentMetrics(agent_name="test")
        m.call_count = 1
        m.prompt_tokens = 500
        m.completion_tokens = 300
        m.total_tokens = 800
        m.total_latency_ms = 150.0
        assert m.avg_latency_ms == 150.0
        assert m.tokens_per_call == 800.0

    def test_record_multiple_calls(self):
        m = AgentMetrics(agent_name="test")
        m.call_count = 3
        m.prompt_tokens = 1500
        m.completion_tokens = 900
        m.total_tokens = 2400
        m.total_latency_ms = 450.0
        assert m.avg_latency_ms == 150.0
        assert m.tokens_per_call == 800.0

    def test_cache_hit_rate(self):
        m = AgentMetrics(agent_name="test")
        m.prompt_tokens = 1000
        m.cached_tokens = 250
        assert m.cache_hit_rate == 0.25

    def test_cache_hit_rate_zero_prompt(self):
        m = AgentMetrics(agent_name="test")
        assert m.cache_hit_rate == 0.0

    def test_to_dict(self):
        m = AgentMetrics(agent_name="research", call_count=2, total_tokens=1600)
        d = m.to_dict()
        assert d["agent"] == "research"
        assert d["calls"] == 2
        assert d["total_tokens"] == 1600


class TestTokenTracker:
    def test_initial_state(self, tracker):
        assert tracker.total_tokens == 0
        assert tracker.total_calls == 0

    def test_record_single(self, tracker):
        tracker.record("research", prompt_tokens=500, completion_tokens=300, latency_ms=100)
        assert tracker.total_tokens == 800
        assert tracker.total_calls == 1

    def test_record_multiple_agents(self, tracker):
        tracker.record("research", prompt_tokens=500, completion_tokens=300, latency_ms=100)
        tracker.record("writer", prompt_tokens=1000, completion_tokens=800, latency_ms=200)
        assert tracker.total_tokens == 2600
        assert tracker.total_calls == 2

    def test_record_accumulates(self, tracker):
        tracker.record("research", prompt_tokens=500, completion_tokens=300, latency_ms=100)
        tracker.record("research", prompt_tokens=600, completion_tokens=400, latency_ms=120)
        assert tracker.total_tokens == 1800
        assert tracker.total_calls == 2

    def test_pipeline_duration(self, tracker):
        import time
        tracker.start_pipeline()
        time.sleep(0.01)
        tracker.end_pipeline()
        assert tracker.pipeline_duration_s > 0

    def test_summary_structure(self, tracker):
        tracker.record("research", prompt_tokens=500, completion_tokens=300, latency_ms=100)
        summary = tracker.summary()
        assert "run_id" in summary
        assert "total_tokens" in summary
        assert "agents" in summary
        assert "research" in summary["agents"]

    def test_report_contains_headers(self, tracker):
        tracker.record("research", prompt_tokens=500, completion_tokens=300, latency_ms=100)
        report = tracker.report()
        assert "Token Consumption Report" in report
        assert "research" in report

    def test_save_creates_file(self, tracker):
        tracker.record("research", prompt_tokens=500, completion_tokens=300, latency_ms=100)
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker._output_dir = tmpdir
            path = tracker.save()
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert data["total_tokens"] == 800

    def test_save_with_custom_path(self, tracker):
        tracker.record("test", prompt_tokens=100, completion_tokens=50, latency_ms=50)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        tracker.save(path)
        with open(path) as f:
            data = json.load(f)
        assert data["total_tokens"] == 150
        os.unlink(path)

    def test_cached_tokens_tracking(self, tracker):
        tracker.record(
            "research", prompt_tokens=500, completion_tokens=300,
            latency_ms=100, cached_tokens=200
        )
        summary = tracker.summary()
        assert summary["agents"]["research"]["cached_tokens"] == 200

    def test_error_tracking(self, tracker):
        tracker.record(
            "research", prompt_tokens=0, completion_tokens=0,
            latency_ms=50, errors=1, retries=2
        )
        summary = tracker.summary()
        assert summary["agents"]["research"]["errors"] == 1
        assert summary["agents"]["research"]["retries"] == 2
