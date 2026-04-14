# tools/

Low-level tool wrappers. Each file exposes one callable tool that agents and skills can register with the Claude API via the `tools` parameter.

## What belongs here

- Thin wrappers around external systems: web search, file I/O, shell commands, database queries, third-party APIs.
- Each tool corresponds to one JSON schema definition that gets passed to `client.messages.create(tools=[...])`.
- No business logic — tools do exactly one thing and return structured JSON.

## Conventions

- Filename matches the tool name: `web-search.ts` → tool name `"web_search"`.
- Every file exports two things:
  1. `definition` — the JSON schema object (name, description, input_schema).
  2. `execute(input)` — the implementation function that runs when the model calls the tool.
- Validate all inputs at the boundary before executing (never trust raw model output passed to shell or SQL).
- Return `{ ok: true, result: ... }` on success and `{ ok: false, error: "..." }` on failure — let the agent decide how to recover.
- Never log secrets, tokens, or full API responses at info level.

## Example structure

```
tools/
├── web-search.ts      # Searches the web via an external API
├── read_file.py       # Reads a file from the local filesystem
├── run_shell.py       # Executes a shell command (argument array only)
└── github_api.ts      # Wraps GitHub REST API endpoints
```

## Testing

Mirror each tool with a test file under `tests/tools/`. Mock all external calls — no live API calls in unit tests.

```
tests/tools/web-search.test.ts
tests/tools/read_file_test.py
```
