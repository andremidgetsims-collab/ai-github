# pipelines/

Multi-step automation workflows. A pipeline wires together agents, skills, and tools into an end-to-end process that can be triggered on a schedule, by a webhook, or manually.

## What belongs here

- Orchestration logic that runs multiple agents in sequence or in parallel.
- Entry points for CI/CD jobs, cron tasks, or event-driven workflows.
- State checkpointing so long-running pipelines are resumable after failure.

## Conventions

- Filename describes the workflow: `nightly-report.ts`, `pr_triage_pipeline.py`.
- Each pipeline has a clearly defined `input` schema and `output` schema.
- Pipelines must be idempotent where possible — re-running with the same input should not cause duplicate side effects.
- Checkpoint intermediate state (to a file or database) after each major step so a crashed pipeline can resume without re-doing completed work.
- Emit structured log lines (`{ step, status, duration_ms }`) at each stage for observability.

## Example structure

```
pipelines/
├── nightly-report.ts       # Generates and sends a nightly digest
├── pr_triage_pipeline.py   # Labels and assigns incoming PRs automatically
└── data_refresh_pipeline.py# Fetches, transforms, and stores external data
```

## Testing

Mirror each pipeline with a test file under `tests/pipelines/`. Use mocked agents/tools to test orchestration logic in isolation.

```
tests/pipelines/nightly-report.test.ts
tests/pipelines/pr_triage_pipeline_test.py
```
