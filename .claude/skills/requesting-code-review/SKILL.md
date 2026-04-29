---
name: requesting-code-review
description: Use when completing a task in subagent-driven development, finishing a major feature, or before merging to main - dispatches a code-reviewer subagent with a structured template
---

# Requesting Code Review

## Overview

Review early, review often. Dispatch a focused code-reviewer subagent after each significant unit of work.

**Core principle:** Never skip reviews for "simple" changes. Code review catches issues that self-review misses.

## When Reviews Are Mandatory

- After completing each task in `subagent-driven-development`
- After finishing a major feature
- Before merge to main

## When Reviews Are Optional (but recommended)

- When stuck on a problem
- Before a significant refactor
- After resolving a complex bug

## The Process

### Step 1: Gather Git SHAs

```bash
# Base SHA (start of your work)
git log --oneline | tail -5

# Current HEAD
git rev-parse HEAD
```

### Step 2: Dispatch Reviewer Subagent

Provide the reviewer with:
- **Base SHA** and **current HEAD SHA**
- **What was implemented** — brief description of the feature/fix
- **Requirements** — what the code is supposed to do
- **Any specific concerns** — areas you're uncertain about

### Step 3: Handle Feedback by Severity

| Severity | Action |
|----------|--------|
| **Critical** | Fix immediately before proceeding |
| **Important** | Fix before moving to next task |
| **Minor** | Document for future attention |

**Never:**
- Skip the review
- Ignore Critical issues
- Proceed with unfixed Important issues

## Pushback

If you believe reviewer feedback is incorrect, push back with:
- Technical reasoning
- Supporting code or tests
- Reference to prior architectural decisions

## Integration

**Called by:**
- **subagent-driven-development** — after each task (both spec compliance and code quality stages)
- **executing-plans** — before completing a batch

**Pairs with:**
- **superpowers:receiving-code-review** — for handling feedback once received
