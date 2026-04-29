#!/usr/bin/env python3
"""
research.py — Run the research agent from the command line.

Usage:
    python tools/research.py "topic goes here"
    python tools/research.py "quantum computing breakthroughs" --debug
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure the project root is on sys.path so agents/ and skills/ are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.research_agent import AgentError, run  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Research a topic and print a formatted Markdown report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  python tools/research.py \"quantum computing breakthroughs\"",
    )
    parser.add_argument("topic", help="The subject to research")
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.WARNING,
        format="%(levelname)s %(name)s — %(message)s",
        stream=sys.stderr,
    )

    try:
        report = run(args.topic)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except AgentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)

    print(report.report)

    # Print metadata to stderr so it doesn't pollute piped output
    print(
        f"\n---\nQueries issued : {len(report.search_queries)}\n"
        f"Sources found  : {len(report.sources)}\n"
        f"Findings       : {len(report.bullets)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
