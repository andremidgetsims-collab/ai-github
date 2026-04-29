"""
Unit tests for research_agent.

Both the web-researcher skill and the Anthropic client are mocked —
no live API calls are made.
"""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from agents.research_agent import AgentError, ResearchReport, _format_report, run

# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

FAKE_RESULT = MagicMock()
FAKE_RESULT.topic = "quantum computing"
FAKE_RESULT.bullets = [
    "Quantum computers use qubits instead of classical bits.",
    "They can solve certain optimisation problems exponentially faster.",
]
FAKE_RESULT.sources = ["https://example.com/quantum"]
FAKE_RESULT.search_queries = ["quantum computing breakthroughs 2024"]

VALID_REPORT = """\
## Executive Summary
Quantum computing leverages quantum mechanics to process information in fundamentally new ways.

## Key Findings
- Quantum computers use qubits instead of classical bits.
- They can solve certain optimisation problems exponentially faster.

## Analysis
The field is advancing rapidly, with both hardware and algorithm improvements driving progress.

## Sources
1. https://example.com/quantum
"""


def _mock_response(text: str) -> MagicMock:
    """Build a minimal mock of an Anthropic messages.create response."""
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


# ---------------------------------------------------------------------------
# run() — input validation
# ---------------------------------------------------------------------------


class TestRunInputValidation:
    def test_raises_on_empty_string(self):
        with pytest.raises(ValueError, match="non-empty"):
            run("")

    def test_raises_on_whitespace_only(self):
        with pytest.raises(ValueError, match="non-empty"):
            run("   ")

    def test_strips_whitespace_from_topic(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response(VALID_REPORT)

        with patch("agents.research_agent._research", return_value=FAKE_RESULT):
            report = run("  quantum computing  ", client=client)

        assert report.topic == "quantum computing"


# ---------------------------------------------------------------------------
# run() — happy path
# ---------------------------------------------------------------------------


class TestRunHappyPath:
    def test_returns_research_report_dataclass(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response(VALID_REPORT)

        with patch("agents.research_agent._research", return_value=FAKE_RESULT):
            report = run("quantum computing", client=client)

        assert isinstance(report, ResearchReport)

    def test_report_fields_populated_correctly(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response(VALID_REPORT)

        with patch("agents.research_agent._research", return_value=FAKE_RESULT):
            report = run("quantum computing", client=client)

        assert report.topic == "quantum computing"
        assert report.report == VALID_REPORT
        assert report.bullets == FAKE_RESULT.bullets
        assert report.sources == FAKE_RESULT.sources
        assert report.search_queries == FAKE_RESULT.search_queries

    def test_passes_client_to_skill(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response(VALID_REPORT)

        with patch("agents.research_agent._research", return_value=FAKE_RESULT) as mock_research:
            run("quantum computing", client=client)

        mock_research.assert_called_once_with("quantum computing", client=client)


# ---------------------------------------------------------------------------
# run() — error handling
# ---------------------------------------------------------------------------


class TestRunErrorHandling:
    def test_environment_error_from_skill_becomes_agent_error(self):
        with patch(
            "agents.research_agent._research",
            side_effect=EnvironmentError("BRAVE_SEARCH_API_KEY is not set"),
        ):
            with pytest.raises(AgentError, match="Search backend is not configured"):
                run("any topic")

    def test_runtime_error_from_skill_becomes_agent_error(self):
        with patch(
            "agents.research_agent._research",
            side_effect=RuntimeError("did not complete within 10 iterations"),
        ):
            with pytest.raises(AgentError, match="Research skill failed"):
                run("any topic")

    def test_formatting_exception_becomes_agent_error(self):
        client = MagicMock()
        client.messages.create.side_effect = Exception("upstream API timeout")

        with patch("agents.research_agent._research", return_value=FAKE_RESULT):
            with pytest.raises(AgentError, match="Report formatting failed"):
                run("any topic", client=client)

    def test_agent_error_chains_original_cause(self):
        original = EnvironmentError("missing key")
        with patch("agents.research_agent._research", side_effect=original):
            with pytest.raises(AgentError) as exc_info:
                run("any topic")

        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# _format_report() — validation and retry logic
# ---------------------------------------------------------------------------


class TestFormatReport:
    def test_returns_immediately_when_all_sections_present(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response(VALID_REPORT)

        report = _format_report(FAKE_RESULT, client)

        assert report == VALID_REPORT
        assert client.messages.create.call_count == 1

    def test_retries_when_sections_missing(self):
        incomplete = (
            "## Executive Summary\nSome summary.\n\n"
            "## Key Findings\n- A point."
            # missing ## Analysis and ## Sources
        )
        client = MagicMock()
        client.messages.create.side_effect = [
            _mock_response(incomplete),
            _mock_response(VALID_REPORT),
        ]

        report = _format_report(FAKE_RESULT, client)

        assert report == VALID_REPORT
        assert client.messages.create.call_count == 2

    def test_revision_message_names_missing_sections(self):
        incomplete = "## Executive Summary\nSummary only."
        client = MagicMock()
        client.messages.create.side_effect = [
            _mock_response(incomplete),
            _mock_response(VALID_REPORT),
        ]

        _format_report(FAKE_RESULT, client)

        second_call_messages = client.messages.create.call_args_list[1][1]["messages"]
        revision_content = second_call_messages[-1]["content"]
        assert "missing" in revision_content.lower()
        assert "## Key Findings" in revision_content

    def test_returns_best_attempt_after_max_iterations(self):
        incomplete = "## Executive Summary\nOnly this section."
        client = MagicMock()
        client.messages.create.return_value = _mock_response(incomplete)

        # Must not raise — returns best attempt
        report = _format_report(FAKE_RESULT, client)

        assert "Executive Summary" in report

    def test_empty_bullets_handled_gracefully(self):
        empty_result = MagicMock()
        empty_result.topic = "empty topic"
        empty_result.bullets = []
        empty_result.sources = []

        client = MagicMock()
        client.messages.create.return_value = _mock_response(VALID_REPORT)

        # Should not raise on empty findings
        report = _format_report(empty_result, client)
        assert report == VALID_REPORT

    def test_prompt_caching_enabled_on_system_prompt(self):
        client = MagicMock()
        client.messages.create.return_value = _mock_response(VALID_REPORT)

        _format_report(FAKE_RESULT, client)

        call_kwargs = client.messages.create.call_args[1]
        system = call_kwargs["system"]
        assert system[0]["cache_control"] == {"type": "ephemeral"}
