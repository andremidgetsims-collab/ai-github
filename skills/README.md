# skills/

Reusable skill modules that agents can invoke. A skill is a higher-level capability composed of one or more tools — it encapsulates a repeatable behaviour (e.g. "summarise a document", "draft a reply") so agents don't re-implement it from scratch.

## What belongs here

- Composable units of capability that more than one agent might need.
- Skills may call the Claude API themselves (e.g. a summarisation skill that makes its own `messages.create` call).
- Skills should be stateless — they take inputs, return outputs, and leave state management to the caller.

## Conventions

- Filename: `kebab-case.ts` or `snake_case.py` describing the capability (e.g. `summarise-document.ts`, `draft_reply.py`).
- Export a single primary function with a clear signature.
- Accept a typed input object; return a typed output object or throw a typed error.
- Pass prompt caching `cache_control` on any large, repeated context the skill sends to Claude.

## Example structure

```
skills/
├── summarise-document.ts  # Condenses long text into bullet points
├── draft_reply.py         # Drafts a reply given a thread and instructions
└── extract_entities.py    # Pulls structured entities from unstructured text
```

## Testing

Mirror each skill with a test file under `tests/skills/`:

```
tests/skills/summarise-document.test.ts
tests/skills/draft_reply_test.py
```
