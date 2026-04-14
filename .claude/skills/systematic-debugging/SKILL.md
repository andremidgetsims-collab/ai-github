---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully** — don't skip past errors or warnings; read stack traces completely
2. **Reproduce Consistently** — can you trigger it reliably? What are the exact steps?
3. **Check Recent Changes** — git diff, recent commits, new dependencies, config changes
4. **Gather Evidence in Multi-Component Systems**

   For each component boundary, add diagnostic instrumentation:
   ```bash
   # Log what data enters component
   # Log what data exits component
   # Verify environment/config propagation
   # Check state at each layer
   ```
   Run once to gather evidence showing WHERE it breaks, THEN investigate that specific component.

5. **Trace Data Flow** — where does bad value originate? Keep tracing up until you find the source. Fix at source, not at symptom.

### Phase 2: Pattern Analysis

1. Find working examples in same codebase
2. Read reference implementation COMPLETELY (don't skim)
3. List every difference between working and broken, however small
4. Understand all dependencies, settings, config, environment

### Phase 3: Hypothesis and Testing

1. **Form Single Hypothesis** — "I think X is the root cause because Y"
2. **Test Minimally** — smallest possible change to test hypothesis, one variable at a time
3. **Verify Before Continuing** — worked? → Phase 4. Didn't work? Form NEW hypothesis.
4. **When You Don't Know** — say so, don't pretend to know

### Phase 4: Implementation

1. **Create Failing Test Case** — simplest possible reproduction (use `superpowers:test-driven-development`)
2. **Implement Single Fix** — address root cause, ONE change at a time, no "while I'm here" improvements
3. **Verify Fix** — test passes? No other tests broken?
4. **If Fix Doesn't Work** — STOP. Count attempts. If ≥ 3: question the architecture (see below)

### When 3+ Fixes Fail: Question Architecture

Pattern indicating architectural problem:
- Each fix reveals new coupling/shared state in a different place
- Fixes require "massive refactoring"
- Each fix creates new symptoms elsewhere

**STOP and discuss with your human partner before attempting more fixes.**

## Red Flags — STOP and Follow Process

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- Adding multiple changes at once
- Proposing solutions before tracing data flow
- "One more fix attempt" (when already tried 2+)
- Each fix reveals new problem in different place

**ALL of these mean: STOP. Return to Phase 1.**

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. |
| "Emergency, no time for process" | Systematic is FASTER than guess-and-check. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "One more fix attempt" (after 2+) | 3+ failures = architectural problem. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |

## Integration

**Related skills:**
- **superpowers:test-driven-development** — for creating failing test case (Phase 4)
- **superpowers:verification-before-completion** — verify fix worked before claiming success
