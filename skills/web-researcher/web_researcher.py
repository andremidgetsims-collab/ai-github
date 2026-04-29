"""
web_researcher.py — Research a topic using web search and Claude.

Entry point: run(topic) -> ResearchResult
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import anthropic
import httpx

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 10

SYSTEM_PROMPT = """\
You are a thorough research assistant. Given a topic:

1. Call web_search one or more times to gather information from multiple angles \
   (definitions, recent developments, statistics, expert opinions).
2. Once you have enough information, output ONLY a JSON object — no prose before \
   or after — with this exact shape:

{
  "bullets": ["concise finding", "another finding", ...],
  "sources": ["https://example.com", ...]
}

Include 5–10 bullet points. Each bullet should be a complete, informative sentence.\
"""

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class ResearchResult:
    topic: str
    bullets: list[str]
    sources: list[str]
    search_queries: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

WEB_SEARCH_TOOL: dict[str, Any] = {
    "name": "web_search",
    "description": (
        "Search the web for current information. "
        "Returns a list of results with titles, URLs, and snippets."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up",
            }
        },
        "required": ["query"],
    },
}

# ---------------------------------------------------------------------------
# Search backend
# ---------------------------------------------------------------------------


def _execute_search(query: str) -> list[dict[str, str]]:
    """
    Execute a web search and return results.

    Returns: [{"title": str, "url": str, "snippet": str}, ...]

    Uses the Brave Search API by default (BRAVE_SEARCH_API_KEY env var).
    Swap this function for any other provider (SerpAPI, Tavily, Exa, etc.) —
    the only contract is the return shape above.
    """
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "BRAVE_SEARCH_API_KEY is not set. "
            "Set it to a Brave Search API key, or replace _execute_search() "
            "with your preferred search provider."
        )

    response = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
        params={"q": query, "count": 5},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", ""),
        }
        for item in data.get("web", {}).get("results", [])
    ]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(topic: str, *, client: anthropic.Anthropic | None = None) -> ResearchResult:
    """
    Research a topic using web search and Claude.

    Args:
        topic:  The subject to research.
        client: Optional Anthropic client (inject a mock in unit tests).

    Returns:
        ResearchResult with bullet-point findings, source URLs, and metadata.

    Raises:
        RuntimeError:     If the loop exceeds MAX_ITERATIONS without completing.
        EnvironmentError: If required environment variables are missing.
    """
    if client is None:
        client = anthropic.Anthropic()

    messages: list[dict[str, Any]] = [
        {"role": "user", "content": f"Research this topic thoroughly: {topic}"},
    ]
    search_queries: list[str] = []

    for _ in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[WEB_SEARCH_TOOL],  # type: ignore[list-item]
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            text = next(
                (block.text for block in response.content if hasattr(block, "text")),
                "{}",
            )
            return _build_result(topic, text, search_queries)

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                query: str = block.input.get("query", "")
                search_queries.append(query)

                try:
                    results = _execute_search(query)
                    content = json.dumps(results)
                    is_error = False
                except Exception as exc:
                    # Surface errors to the model as tool results so it can recover
                    content = json.dumps({"error": str(exc)})
                    is_error = True

                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content,
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(
        f"Research on '{topic}' did not complete within {MAX_ITERATIONS} iterations."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_result(
    topic: str, text: str, search_queries: list[str]
) -> ResearchResult:
    """Parse the model's final JSON response into a ResearchResult."""
    try:
        cleaned = (
            text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        data = json.loads(cleaned)
        bullets: list[str] = data.get("bullets", [])
        sources: list[str] = data.get("sources", [])
    except json.JSONDecodeError:
        # Graceful fallback: treat non-empty lines as bullets
        bullets = [line.lstrip("•-* ").strip() for line in text.splitlines() if line.strip()]
        sources = []

    return ResearchResult(
        topic=topic,
        bullets=bullets,
        sources=sources,
        search_queries=search_queries,
    )
