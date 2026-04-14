"""
research_agent.py — Orchestrates web research and formats a polished report.

Calls the web-researcher skill to gather findings, then uses Claude to
produce a structured Markdown report with an executive summary, key findings,
analysis, and sources.

Entry point: run(topic) -> ResearchReport
"""

from __future__ import annotations

import importlib.util
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Skill import
# The skill directory uses kebab-case (web-researcher), which is not a valid
# Python identifier, so we load it by file path rather than a standard import.
# ---------------------------------------------------------------------------

_SKILL_PATH = (
    Path(__file__).parent.parent / "skills" / "web-researcher" / "web_researcher.py"
)
_spec = importlib.util.spec_from_file_location("web_researcher", _SKILL_PATH)
_skill_module = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_skill_module)  # type: ignore[union-attr]

_research = _skill_module.run  # (topic, *, client) -> ResearchResult

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 3  # max refinement passes for the formatting step

LOG = logging.getLogger(__name__)

REQUIRED_SECTIONS = [
    "## Executive Summary",
    "## Key Findings",
    "## Analysis",
    "## Sources",
]

REPORT_SYSTEM_PROMPT = """\
You are a professional research writer. You will be given research findings on a topic.

Produce a polished report in Markdown using exactly these four sections, in order:

## Executive Summary
2–3 sentences summarising the topic and the most important findings.

## Key Findings
The provided bullet points, lightly edited for clarity. Group related points under
sub-headings if there are clear themes.

## Analysis
1–2 paragraphs interpreting what the findings mean and why they matter.

## Sources
A numbered list of the source URLs.

Rules:
- Use only facts present in the provided findings — do not invent information.
- Write for a technically literate audience.
- Be concise and direct.\
"""

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class ResearchReport:
    topic: str
    report: str                          # Formatted Markdown
    bullets: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)


class AgentError(Exception):
    """Raised when the research agent cannot complete its task."""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(topic: str, *, client: anthropic.Anthropic | None = None) -> ResearchReport:
    """
    Research a topic and return a formatted Markdown report.

    Args:
        topic:  The subject to research.
        client: Optional Anthropic client (inject a mock in unit tests).

    Returns:
        ResearchReport containing the formatted report and raw research metadata.

    Raises:
        ValueError:   If topic is blank.
        AgentError:   If the skill or formatting step cannot complete.
    """
    topic = topic.strip()
    if not topic:
        raise ValueError("topic must be a non-empty string")

    if client is None:
        client = anthropic.Anthropic()

    LOG.info("Research agent starting — topic: %r", topic)

    # Step 1: gather research via the web-researcher skill
    try:
        result = _research(topic, client=client)
    except EnvironmentError as exc:
        raise AgentError(f"Search backend is not configured: {exc}") from exc
    except RuntimeError as exc:
        raise AgentError(f"Research skill failed: {exc}") from exc

    LOG.info(
        "Research complete — %d findings, %d sources, %d queries",
        len(result.bullets),
        len(result.sources),
        len(result.search_queries),
    )

    # Step 2: format findings into a polished report
    try:
        report_text = _format_report(result, client)
    except Exception as exc:
        raise AgentError(f"Report formatting failed: {exc}") from exc

    LOG.info("Report ready — topic: %r", topic)

    return ResearchReport(
        topic=topic,
        report=report_text,
        bullets=result.bullets,
        sources=result.sources,
        search_queries=result.search_queries,
    )


# ---------------------------------------------------------------------------
# Formatting step
# ---------------------------------------------------------------------------


def _format_report(result: Any, client: anthropic.Anthropic) -> str:
    """
    Use Claude to format raw research findings into a Markdown report.

    Validates that all four required sections are present and retries up to
    MAX_ITERATIONS times with a revision prompt if any are missing.
    Returns the best attempt when the limit is reached.

    Args:
        result: ResearchResult from the web-researcher skill.
        client: Anthropic client.

    Returns:
        Formatted Markdown report.
    """
    findings_block = (
        "\n".join(f"- {b}" for b in result.bullets) or "(no findings available)"
    )
    sources_block = "\n".join(result.sources) or "(no sources available)"

    user_content = (
        f"Topic: {result.topic}\n\n"
        f"Findings:\n{findings_block}\n\n"
        f"Sources:\n{sources_block}\n\n"
        "Write the research report now."
    )

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_content}]
    last_report = ""

    for iteration in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": REPORT_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=messages,
        )

        last_report = next(
            (block.text for block in response.content if hasattr(block, "text")),
            "",
        )

        missing = [s for s in REQUIRED_SECTIONS if s not in last_report]
        if not missing:
            LOG.debug("Report validated on iteration %d", iteration + 1)
            return last_report

        LOG.debug(
            "Iteration %d — report missing sections: %s — requesting revision",
            iteration + 1,
            missing,
        )
        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"The report is missing these required sections: {missing}. "
                    "Please revise it to include all four sections."
                ),
            }
        )

    LOG.warning(
        "Report did not satisfy all requirements within %d iterations — "
        "returning best attempt",
        MAX_ITERATIONS,
    )
    return last_report
