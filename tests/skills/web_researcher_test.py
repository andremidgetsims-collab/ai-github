"""Unit tests for the web-researcher skill.

The Anthropic client and search backend are both mocked — no live API calls.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from skills.web_researcher.web_researcher import (
    ResearchResult,
    _build_result,
    run,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_use_block(tool_use_id: str, query: str) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_use_id
    block.input = {"query": query}
    return block


def _text_block(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _response(stop_reason: str, *blocks: MagicMock) -> MagicMock:
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = list(blocks)
    return resp


FINAL_JSON = json.dumps(
    {
        "bullets": ["Quantum computers use qubits.", "They can factor large numbers quickly."],
        "sources": ["https://example.com/quantum"],
    }
)

SEARCH_RESULTS = [
    {"title": "Quantum basics", "url": "https://example.com/quantum", "snippet": "Intro to qubits."}
]


# ---------------------------------------------------------------------------
# _build_result
# ---------------------------------------------------------------------------


class TestBuildResult:
    def test_parses_valid_json(self):
        result = _build_result("quantum", FINAL_JSON, ["quantum computing"])
        assert result.topic == "quantum"
        assert result.bullets == ["Quantum computers use qubits.", "They can factor large numbers quickly."]
        assert result.sources == ["https://example.com/quantum"]
        assert result.search_queries == ["quantum computing"]

    def test_strips_markdown_fences(self):
        fenced = f"```json\n{FINAL_JSON}\n```"
        result = _build_result("topic", fenced, [])
        assert result.bullets[0] == "Quantum computers use qubits."

    def test_fallback_on_invalid_json(self):
        result = _build_result("topic", "- Finding one\n- Finding two", [])
        assert len(result.bullets) == 2
        assert result.sources == []

    def test_empty_response_returns_empty_bullets(self):
        result = _build_result("topic", "{}", [])
        assert result.bullets == []
        assert result.sources == []


# ---------------------------------------------------------------------------
# run() — happy path
# ---------------------------------------------------------------------------


class TestRunHappyPath:
    def test_single_search_then_answer(self):
        client = MagicMock()
        client.messages.create.side_effect = [
            _response("tool_use", _tool_use_block("tu_1", "quantum computing")),
            _response("end_turn", _text_block(FINAL_JSON)),
        ]

        with patch(
            "skills.web_researcher.web_researcher._execute_search",
            return_value=SEARCH_RESULTS,
        ):
            result = run("quantum computing", client=client)

        assert isinstance(result, ResearchResult)
        assert result.topic == "quantum computing"
        assert len(result.bullets) == 2
        assert result.search_queries == ["quantum computing"]
        assert client.messages.create.call_count == 2

    def test_multiple_searches_before_answer(self):
        client = MagicMock()
        client.messages.create.side_effect = [
            _response("tool_use", _tool_use_block("tu_1", "query one")),
            _response("tool_use", _tool_use_block("tu_2", "query two")),
            _response("end_turn", _text_block(FINAL_JSON)),
        ]

        with patch(
            "skills.web_researcher.web_researcher._execute_search",
            return_value=SEARCH_RESULTS,
        ):
            result = run("multi-step topic", client=client)

        assert result.search_queries == ["query one", "query two"]
        assert client.messages.create.call_count == 3

    def test_immediate_answer_no_search(self):
        """Model returns end_turn on the first call (no tool use)."""
        client = MagicMock()
        client.messages.create.return_value = _response(
            "end_turn", _text_block(FINAL_JSON)
        )

        result = run("simple topic", client=client)

        assert result.search_queries == []
        assert client.messages.create.call_count == 1


# ---------------------------------------------------------------------------
# run() — error handling
# ---------------------------------------------------------------------------


class TestRunErrorHandling:
    def test_search_error_is_surfaced_to_model_not_raised(self):
        """A failing search should not raise — it becomes an is_error tool result."""
        client = MagicMock()
        client.messages.create.side_effect = [
            _response("tool_use", _tool_use_block("tu_1", "bad query")),
            _response("end_turn", _text_block(FINAL_JSON)),
        ]

        with patch(
            "skills.web_researcher.web_researcher._execute_search",
            side_effect=EnvironmentError("BRAVE_SEARCH_API_KEY is not set"),
        ):
            result = run("some topic", client=client)

        # Must not raise — error was passed to the model
        assert isinstance(result, ResearchResult)

        # Verify the tool result sent to the model flagged is_error
        second_call_messages = client.messages.create.call_args_list[1][1]["messages"]
        tool_result = second_call_messages[-1]["content"][0]
        assert tool_result["is_error"] is True

    def test_raises_runtime_error_after_max_iterations(self):
        always_tool_use = _response("tool_use", _tool_use_block("tu_x", "loop query"))
        client = MagicMock()
        client.messages.create.return_value = always_tool_use

        with patch(
            "skills.web_researcher.web_researcher._execute_search",
            return_value=[],
        ):
            with pytest.raises(RuntimeError, match="did not complete"):
                run("infinite topic", client=client)
