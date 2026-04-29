# agents/

Standalone agent implementations. Each file in this directory is a self-contained agent that orchestrates one or more tools to accomplish a specific goal.

## What belongs here

- **One agent per file** — each agent has a clear, single responsibility.
- Agents own the agentic loop: they call the Claude API, decide which tools to invoke, and handle multi-turn conversations.
- Agents import tools from `../tools/` and skills from `../skills/` — they do not reimplement low-level logic.

## Conventions

- Filename: `kebab-case.ts` or `snake_case.py` describing what the agent does (e.g. `code-review-agent.ts`, `search_agent.py`).
- Every agent must export/expose a single entry-point function (e.g. `run(input)`) so it can be called from pipelines or tests.
- Set a hard `MAX_ITERATIONS` constant at the top of each file (default: `20`).
- Log every tool call and result at `debug` level.
- Surface tool errors back to the model as tool results — do not throw and crash the loop.

## Example structure

```
agents/
├── code-review-agent.ts   # Reviews a PR diff and posts comments
├── search_agent.py        # Answers questions using web search
└── triage_agent.py        # Classifies and routes incoming issues
```

## Testing

Mirror each agent with a test file under `tests/agents/`:

```
tests/agents/code-review-agent.test.ts
tests/agents/search_agent_test.py
```
