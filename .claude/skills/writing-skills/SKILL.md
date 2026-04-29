---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment
---

# Writing Skills

## Overview

**Writing skills IS Test-Driven Development applied to process documentation.**

You write test cases (pressure scenarios with subagents), watch them fail (baseline behavior), write the skill (documentation), watch tests pass (agents comply), and refactor (close loopholes).

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

**REQUIRED BACKGROUND:** You MUST understand superpowers:test-driven-development before using this skill.

## What is a Skill?

A **skill** is a reference guide for proven techniques, patterns, or tools.

**Skills are:** Reusable techniques, patterns, tools, reference guides

**Skills are NOT:** Narratives about how you solved a problem once

## SKILL.md Structure

**Frontmatter (YAML):**
- `name`: letters, numbers, hyphens only
- `description`: "Use when..." — triggering conditions ONLY, never workflow summary

**CRITICAL:** Description must describe ONLY when to trigger the skill, not what it does. Descriptions that summarize workflow cause Claude to follow the description instead of reading the full skill.

```yaml
# ❌ BAD: Summarizes workflow
description: Use when executing plans - dispatches subagent per task with code review

# ✅ GOOD: Just triggering conditions
description: Use when executing implementation plans with independent tasks in the current session
```

## The Iron Law (Same as TDD)

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

Write skill before testing? Delete it. Start over.

## RED-GREEN-REFACTOR for Skills

**RED:** Run pressure scenario WITHOUT the skill. Document exact rationalizations agents use.

**GREEN:** Write minimal skill addressing those specific violations. Run scenarios WITH skill.

**REFACTOR:** Find new rationalizations → add explicit counters → re-test until bulletproof.

## Skill Creation Checklist

- [ ] Run baseline scenario WITHOUT skill (RED)
- [ ] Name uses only letters, numbers, hyphens
- [ ] Description starts with "Use when..." — triggering conditions only
- [ ] Description in third person, no workflow summary
- [ ] Address specific failures identified in RED
- [ ] Run scenarios WITH skill — verify compliance (GREEN)
- [ ] Close loopholes (REFACTOR)
- [ ] Build rationalization table from all test iterations
- [ ] Commit and push

## When to Create a Skill

**Create when:**
- Technique wasn't intuitively obvious
- You'd reference this across projects
- Pattern applies broadly

**Don't create for:**
- One-off solutions
- Project-specific conventions (put in CLAUDE.md)
- Things enforceable with automation
