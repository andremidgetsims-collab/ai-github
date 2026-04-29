# web-researcher

Researches any topic by driving Claude to issue web searches, gather information from multiple sources, and synthesise findings into structured bullet-point output.

---

## Input

| Field   | Type   | Required | Description                          |
|---------|--------|----------|--------------------------------------|
| `topic` | `str`  | yes      | The subject or question to research  |

---

## Output — `ResearchResult`

| Field            | Type        | Description                                        |
|------------------|-------------|----------------------------------------------------|
| `topic`          | `str`       | The input topic, echoed back                       |
| `bullets`        | `list[str]` | 5–10 concise findings, each a complete sentence    |
| `sources`        | `list[str]` | URLs of pages consulted during research            |
| `search_queries` | `list[str]` | Web-search queries the model chose to issue        |

---

## Usage

```python
from skills.web_researcher import run

result = run("breakthroughs in quantum computing 2024")

for bullet in result.bullets:
    print(f"• {bullet}")

print("\nSources:")
for url in result.sources:
    print(f"  {url}")
```

---

## Configuration

| Environment variable   | Required | Description                                    |
|------------------------|----------|------------------------------------------------|
| `ANTHROPIC_API_KEY`    | yes      | Anthropic API key                              |
| `BRAVE_SEARCH_API_KEY` | yes      | Brave Search API key (default search backend)  |

### Swapping the search backend

The search logic is isolated in `_execute_search()` in `web_researcher.py`.
Replace it with any provider (SerpAPI, Tavily, Exa, etc.) by matching the contract:

```python
def _execute_search(query: str) -> list[dict[str, str]]:
    # must return: [{"title": str, "url": str, "snippet": str}, ...]
```

---

## How it works

```
run(topic)
  │
  ├─► Claude receives topic + web_search tool definition
  │
  ├─► [loop, max 10 iterations]
  │     ├─ stop_reason == "tool_use"  → execute _execute_search(), feed results back
  │     └─ stop_reason == "end_turn"  → parse final JSON response → return ResearchResult
  │
  └─► RuntimeError if loop exhausted without end_turn
```

1. Claude decides which queries to run and calls `web_search` autonomously.
2. Each search result is fed back as a `tool_result` message.
3. Errors from `_execute_search` are returned to Claude as `is_error: true` tool results — the model can recover rather than crashing the loop.
4. On `end_turn`, Claude's response is expected to be a JSON object (`bullets` + `sources`). A fallback parser handles malformed output gracefully.

---

## Model & caching

- **Model**: `claude-sonnet-4-6` — balanced capability and speed for agentic tasks.
- **Prompt caching**: the system prompt is sent with `cache_control: ephemeral`, reducing latency and cost on repeated calls to the same skill.

---

## Tests

| File | Type |
|------|------|
| `tests/skills/web_researcher_test.py` | Unit tests — mocked client and search backend |
| `tests/integration/web_researcher_test.py` | Integration test — live API (requires `RUN_INTEGRATION=true`) |
