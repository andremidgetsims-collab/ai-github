---
name: writing-plans
description: Use after brainstorming produces an approved spec, to create a detailed task-by-task implementation plan before execution begins
---

# Writing Plans

## Overview

Create detailed, task-by-task implementation plans that a skilled engineer can execute without asking clarifying questions.

**Core principle:** Every step must contain the actual content needed — no placeholders, no "TBD", no "add error handling".

## Plan Structure

### 1. File Map
List every file to create or modify upfront with clear responsibility boundaries.

### 2. Tasks (bite-sized, 2–5 minutes each)
Each task follows TDD discipline:
1. Write failing test (exact code, exact file path)
2. Run test — confirm it fails
3. Write minimal implementation to pass
4. Run test — confirm it passes
5. Commit

### 3. Quality Requirements for Each Step
- **Exact file paths** — no ambiguity
- **Complete code examples** — no fill-in-the-blank
- **Exact command output** expected from verifications
- **Type consistency** — types used in task N are defined in task N or earlier
- **No cross-references** — "similar to Task N" is forbidden; repeat the code

## Self-Review Checklist (mandatory before handoff)

- [ ] Every spec requirement is covered by at least one task
- [ ] No placeholders ("TBD", "add error handling", "implement later")
- [ ] All types used are defined
- [ ] No vague instructions ("handle edge cases", "clean up")
- [ ] Each task takes 2–5 minutes, not 30
- [ ] Plan covers one cohesive subsystem (split if it spans multiple independent areas)

## Output Location

```
docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md
```

## Handoff Options

Present the user with a choice after plan is written:

1. **Subagent-Driven** — fresh subagent per task with two-stage review (recommended)
   → Use `superpowers:subagent-driven-development`

2. **Inline Execution** — batch with checkpoints in current session
   → Use `superpowers:executing-plans`

## Red Flags

**Never:**
- Write "TBD" or "add error handling" in a plan step
- Reference another task instead of repeating code
- Leave types undefined
- Write tasks that take more than 5 minutes
- Hand off a plan before self-review checklist passes

## Integration

**Called by:**
- **superpowers:brainstorming** — after design is fully approved

**Hands off to:**
- **superpowers:subagent-driven-development** (recommended)
- **superpowers:executing-plans** (inline session)

**Requires:**
- **superpowers:using-git-worktrees** — isolated workspace must be set up before execution starts
