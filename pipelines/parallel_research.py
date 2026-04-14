"""
parallel_research.py — Run research_agent.run() on multiple topics concurrently.

Each topic runs in its own thread. Failures are isolated per topic — one agent
error does not abort the others. All results (successful and failed) are returned
together in a PipelineResult.

Entry point: run(topics) -> PipelineResult
"""

from __future__ import annotations

import logging
import sys
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import anthropic

# Ensure project root is on sys.path so agents/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.research_agent import AgentError, ResearchReport  # noqa: E402
from agents.research_agent import run as _agent_run           # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class TopicResult:
    """Outcome for a single topic — exactly one of report/error is set."""

    topic: str
    report: ResearchReport | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.report is not None


@dataclass
class PipelineResult:
    """Aggregated results from all topics."""

    results: list[TopicResult] = field(default_factory=list)

    @property
    def succeeded(self) -> list[TopicResult]:
        return [r for r in self.results if r.ok]

    @property
    def failed(self) -> list[TopicResult]:
        return [r for r in self.results if not r.ok]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run(
    topics: Sequence[str],
    *,
    max_workers: int | None = None,
    client: anthropic.Anthropic | None = None,
) -> PipelineResult:
    """
    Run research_agent.run() on each topic concurrently.

    Args:
        topics:      Non-empty sequence of topics to research.
        max_workers: Thread pool size. Defaults to len(topics) so all topics
                     start immediately. Cap this if you need to limit concurrency.
        client:      Optional shared Anthropic client (thread-safe). A new
                     client is created if not provided.

    Returns:
        PipelineResult with one TopicResult per topic, in input order.
        Failed topics carry an error string; the pipeline never raises.

    Raises:
        ValueError: If topics is empty or contains blank strings.
    """
    topics = [t.strip() for t in topics]
    if not topics:
        raise ValueError("topics must be a non-empty sequence")
    blank = [t for t in topics if not t]
    if blank:
        raise ValueError(f"topics must not contain blank strings (got {len(blank)} blank)")

    if client is None:
        client = anthropic.Anthropic()

    workers = max_workers if max_workers is not None else len(topics)
    LOG.info("Pipeline starting — %d topics, %d workers", len(topics), workers)

    # Map future -> original topic so results can be re-ordered
    future_to_topic: dict[Future[ResearchReport], str] = {}

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for topic in topics:
            future = executor.submit(_agent_run, topic, client=client)
            future_to_topic[future] = topic
            LOG.debug("Submitted: %r", topic)

        topic_results: dict[str, TopicResult] = {}

        for future in as_completed(future_to_topic):
            topic = future_to_topic[future]
            try:
                report = future.result()
                topic_results[topic] = TopicResult(topic=topic, report=report)
                LOG.info("Completed: %r", topic)
            except (AgentError, ValueError) as exc:
                topic_results[topic] = TopicResult(topic=topic, error=str(exc))
                LOG.warning("Failed:    %r — %s", topic, exc)
            except Exception as exc:  # unexpected errors also isolated
                topic_results[topic] = TopicResult(topic=topic, error=f"unexpected error: {exc}")
                LOG.error("Error:     %r — %s", topic, exc)

    # Restore original topic order
    ordered = [topic_results[t] for t in topics]

    result = PipelineResult(results=ordered)
    LOG.info(
        "Pipeline complete — %d succeeded, %d failed",
        len(result.succeeded),
        len(result.failed),
    )
    return result
