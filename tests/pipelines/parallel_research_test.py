"""
Unit tests for parallel_research pipeline.

research_agent.run() is mocked — no live API calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.research_agent import AgentError, ResearchReport
from pipelines.parallel_research import PipelineResult, TopicResult, run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_report(topic: str) -> ResearchReport:
    return ResearchReport(
        topic=topic,
        report=f"## Executive Summary\nReport for {topic}.\n\n"
               "## Key Findings\n- Finding.\n\n"
               "## Analysis\nAnalysis.\n\n"
               "## Sources\n1. https://example.com",
        bullets=["Finding."],
        sources=["https://example.com"],
        search_queries=[f"{topic} query"],
    )


TOPICS = ["quantum computing", "climate change", "large language models"]


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_raises_on_empty_list(self):
        with pytest.raises(ValueError, match="non-empty"):
            run([])

    def test_raises_on_blank_topic(self):
        with pytest.raises(ValueError, match="blank"):
            run(["valid topic", "   ", "another topic"])

    def test_strips_whitespace_from_topics(self):
        reports = {t: _fake_report(t) for t in TOPICS}
        with patch("pipelines.parallel_research._agent_run", side_effect=lambda t, **_: reports[t]):
            result = run(["  quantum computing  ", "climate change", "large language models"])

        assert result.results[0].topic == "quantum computing"


# ---------------------------------------------------------------------------
# All topics succeed
# ---------------------------------------------------------------------------

class TestAllSucceed:
    def test_returns_pipeline_result(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=lambda t, **_: _fake_report(t),
        ):
            result = run(TOPICS)

        assert isinstance(result, PipelineResult)

    def test_one_result_per_topic(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=lambda t, **_: _fake_report(t),
        ):
            result = run(TOPICS)

        assert len(result.results) == 3

    def test_results_preserve_input_order(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=lambda t, **_: _fake_report(t),
        ):
            result = run(TOPICS)

        assert [r.topic for r in result.results] == TOPICS

    def test_all_results_ok(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=lambda t, **_: _fake_report(t),
        ):
            result = run(TOPICS)

        assert len(result.succeeded) == 3
        assert len(result.failed) == 0

    def test_report_fields_populated(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=lambda t, **_: _fake_report(t),
        ):
            result = run(TOPICS)

        for topic_result in result.results:
            assert topic_result.ok
            assert topic_result.report is not None
            assert topic_result.error is None
            assert topic_result.report.topic == topic_result.topic


# ---------------------------------------------------------------------------
# Partial failure — one topic fails, others succeed
# ---------------------------------------------------------------------------

class TestPartialFailure:
    def _side_effect(self, failing_topic: str):
        def _run(topic: str, **_):
            if topic == failing_topic:
                raise AgentError("Search backend is not configured: missing key")
            return _fake_report(topic)
        return _run

    def test_failed_topic_carries_error_string(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=self._side_effect("climate change"),
        ):
            result = run(TOPICS)

        failed = next(r for r in result.results if r.topic == "climate change")
        assert not failed.ok
        assert failed.report is None
        assert "Search backend is not configured" in failed.error

    def test_other_topics_still_succeed(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=self._side_effect("climate change"),
        ):
            result = run(TOPICS)

        assert len(result.succeeded) == 2
        assert len(result.failed) == 1

    def test_succeeded_and_failed_properties(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=self._side_effect("climate change"),
        ):
            result = run(TOPICS)

        assert {r.topic for r in result.succeeded} == {
            "quantum computing", "large language models"
        }
        assert result.failed[0].topic == "climate change"


# ---------------------------------------------------------------------------
# All topics fail
# ---------------------------------------------------------------------------

class TestAllFail:
    def test_pipeline_does_not_raise(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=AgentError("all broken"),
        ):
            result = run(TOPICS)  # must not raise

        assert len(result.failed) == 3
        assert len(result.succeeded) == 0

    def test_unexpected_exception_isolated(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=RuntimeError("unexpected crash"),
        ):
            result = run(TOPICS)

        for r in result.results:
            assert not r.ok
            assert "unexpected error" in r.error


# ---------------------------------------------------------------------------
# max_workers and shared client
# ---------------------------------------------------------------------------

class TestConfiguration:
    def test_custom_max_workers_accepted(self):
        with patch(
            "pipelines.parallel_research._agent_run",
            side_effect=lambda t, **_: _fake_report(t),
        ):
            result = run(TOPICS, max_workers=1)

        assert len(result.succeeded) == 3

    def test_shared_client_forwarded_to_agent(self):
        shared_client = MagicMock()
        captured = []

        def _capture(topic, *, client, **_):
            captured.append(client)
            return _fake_report(topic)

        with patch("pipelines.parallel_research._agent_run", side_effect=_capture):
            run(TOPICS, client=shared_client)

        assert all(c is shared_client for c in captured)
