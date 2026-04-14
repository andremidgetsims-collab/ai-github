---
name: receiving-code-review
description: Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation
---

# Code Review Reception

## Overview

Code review requires technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming. Technical correctness over social comfort.

## The Response Pattern

```
1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

## Forbidden Responses

**NEVER:**
- "You're absolutely right!" (performative)
- "Great point!" / "Excellent feedback!"
- "Let me implement that now" (before verification)
- Any gratitude expression ("Thanks for catching that!")

**INSTEAD:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if wrong
- Just start working (actions > words)

## Handling Unclear Feedback

If any item is unclear: STOP — do not implement anything yet. Ask for clarification on all unclear items before proceeding.

## Source-Specific Handling

### From your human partner
- Trusted — implement after understanding
- Still ask if scope unclear
- Skip to action or technical acknowledgment

### From External Reviewers
Before implementing:
1. Check: Technically correct for THIS codebase?
2. Check: Breaks existing functionality?
3. Check: Reason for current implementation?
4. Check: Does reviewer understand full context?

If suggestion seems wrong: Push back with technical reasoning.

## When To Push Back

Push back when:
- Suggestion breaks existing functionality
- Reviewer lacks full context
- Violates YAGNI (unused feature)
- Technically incorrect for this stack
- Conflicts with your human partner's architectural decisions

## Acknowledging Correct Feedback

```
✅ "Fixed. [Brief description of what changed]"
✅ "Good catch - [specific issue]. Fixed in [location]."
✅ [Just fix it and show in the code]

❌ "You're absolutely right!"
❌ "Great point!" / "Thanks for [anything]"
```

## GitHub Thread Replies

When replying to inline review comments on GitHub, reply in the comment thread, not as a top-level PR comment.

## The Bottom Line

**External feedback = suggestions to evaluate, not orders to follow.**

Verify. Question. Then implement. No performative agreement. Technical rigor always.
