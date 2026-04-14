# tests/

All tests for the project. The directory structure mirrors the source layout so every source file has a predictable test location.

## Structure

```
tests/
├── agents/       # Tests for agents/
├── skills/       # Tests for skills/
├── tools/        # Tests for tools/
├── pipelines/    # Tests for pipelines/
└── integration/  # Live-API integration tests (skipped in CI by default)
```

## Test types

### Unit tests (`tests/{agents,skills,tools,pipelines}/`)

- Mock the Anthropic client — **no live API calls**.
- Fast, deterministic, run on every commit.
- Cover the happy path, error paths, and edge cases.
- Use dependency injection or module mocks to replace external services.

### Integration tests (`tests/integration/`)

- Make real calls to the Claude API and any external services.
- **Skipped unless** `RUN_INTEGRATION=true` is set in the environment.
- Run in a dedicated CI job or locally before release.
- Keep them few and focused — they are slow and cost money.

## Running tests

```bash
# Unit tests only (default)
npm test          # or: pytest

# Include integration tests
RUN_INTEGRATION=true npm test   # or: RUN_INTEGRATION=true pytest
```

## Conventions

- Test filenames mirror source: `agents/my-agent.ts` → `tests/agents/my-agent.test.ts`.
- Each source file needs **at least one unit test and one integration test**.
- Prefer many small, focused test cases over large end-to-end scenarios in unit tests.
- Assert on observable outputs (return values, mock call args); avoid asserting on internal implementation details.
