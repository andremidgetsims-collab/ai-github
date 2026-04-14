# CLAUDE.md

## Project Overview

This is an AI development workspace for building agents, skills, and automation tools using the Claude API and Anthropic SDK. The repo houses reusable agent patterns, skill definitions, and end-to-end automation pipelines.

---

## Repository Layout

```
.
├── agents/          # Standalone agent implementations
├── skills/          # Reusable skill modules invoked by agents
├── tools/           # Low-level tool wrappers (API calls, file I/O, shell)
├── pipelines/       # Multi-step automation workflows
├── tests/           # Unit and integration tests (mirrors src structure)
├── scripts/         # Dev/ops helper scripts
└── CLAUDE.md
```

---

## Development Commands

```bash
# Install dependencies
npm install          # or: pip install -r requirements.txt

# Run all tests
npm test             # or: pytest

# Lint & format
npm run lint         # or: ruff check . && ruff format --check .
npm run format       # or: ruff format .

# Type check
npm run typecheck    # or: pyright / mypy .

# Run a specific agent locally
node agents/my-agent.js   # or: python agents/my_agent.py
```

> Always run lint + typecheck before committing.

---

## Claude API Best Practices

### Model Selection

Default to the most capable available model. Current hierarchy:

| Use case | Model |
|---|---|
| Complex reasoning, planning, code gen | `claude-opus-4-6` |
| Balanced tasks, agents, tool use | `claude-sonnet-4-6` |
| Fast, lightweight classification / routing | `claude-haiku-4-5-20251001` |

### Prompt Caching

Enable prompt caching on all large, repeated context blocks (system prompts, tool schemas, documents). This cuts latency and cost significantly.

```python
# Python example — cache_control on a large system prompt
messages = [{"role": "user", "content": "..."}]
response = client.messages.create(
    model="claude-sonnet-4-6",
    system=[{
        "type": "text",
        "text": LARGE_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }],
    messages=messages,
    max_tokens=1024,
)
```

Always cache:
- System prompts longer than ~1 000 tokens
- Tool/skill schemas passed on every turn
- Retrieved documents used as grounding context

### Tool Use

- Define tools with precise, minimal JSON schemas — no optional fields unless necessary.
- Keep tool descriptions action-oriented (verb + object): `"Search the web for recent news"`.
- Validate all tool inputs at the boundary; never trust raw model output passed directly to shell commands.
- Return structured JSON from tools so the model can reason over results reliably.

### Agentic Loops

- Set a hard `max_iterations` limit on every agent loop (default: 20).
- Log each tool call + result for debugging.
- Surface errors to the model as tool results, not exceptions — let the model recover.
- For long-running tasks, checkpoint state so runs are resumable.

---

## Coding Conventions

### General

- Keep files focused: one agent, one skill, or one tool per file.
- Prefer pure functions; isolate side effects (API calls, file writes) at the edges.
- No magic strings — define model IDs and other constants in a shared `config` module.
- Delete dead code; do not comment it out.

### Naming

| Thing | Convention |
|---|---|
| Files | `kebab-case.ts` / `snake_case.py` |
| Functions / variables | `camelCase` (TS) / `snake_case` (Python) |
| Classes | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` |

### Error Handling

- Only validate at system boundaries (user input, external APIs, file I/O).
- Don't add try/catch for situations that should never happen — let them crash loudly.
- Include enough context in error messages to diagnose without a debugger.

### Security

- Never log API keys, tokens, or secrets.
- Never pass unsanitized user input to shell commands — use argument arrays, not string interpolation.
- Store all credentials in environment variables; never hard-code them.
- Treat model output as untrusted input when it feeds back into system calls.

---

## Testing

- Every agent and skill must have at least one unit test and one integration test.
- Mock the Anthropic client in unit tests — do not make live API calls in CI.
- Integration tests (live API) live in `tests/integration/` and are skipped unless `RUN_INTEGRATION=true`.
- Test filenames mirror source: `agents/my-agent.ts` → `tests/agents/my-agent.test.ts`.

---

## Git Workflow

- **Branch**: `claude/<short-description>` for Claude-authored changes.
- **Commits**: imperative mood, present tense — `"Add retry logic to search tool"`.
- **PRs**: squash-merge preferred; link the issue in the PR body.
- **Never** commit `.env` files, secrets, or large binary assets.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API authentication |
| `LOG_LEVEL` | Logging verbosity (`debug` \| `info` \| `warn` \| `error`) |
| `RUN_INTEGRATION` | Set to `true` to enable live-API integration tests |

Copy `.env.example` to `.env` and fill in values before running locally.
