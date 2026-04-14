---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

Follow this priority order:

1. Check for `.worktrees/` or `worktrees/` directory (`.worktrees` wins if both exist)
2. Check `CLAUDE.md` for a worktree directory preference
3. If neither: ask the user

## Safety Verification

For project-local directories, **always verify the directory is git-ignored before creating:**

```bash
git check-ignore -q .worktrees 2>/dev/null
```

If NOT ignored: add it to `.gitignore`, commit, then proceed.

## Creation Steps

```bash
# Create worktree with new branch
git worktree add .worktrees/<branch-name> -b <branch-name>
cd .worktrees/<branch-name>

# Auto-detect and run project setup
[ -f package.json ] && npm install
[ -f requirements.txt ] && pip install -r requirements.txt
[ -f Cargo.toml ] && cargo build

# Verify clean baseline
npm test / pytest / cargo test
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check CLAUDE.md → Ask user |
| Directory not ignored | Add to .gitignore + commit |
| Tests fail during baseline | Report failures + ask |

## Red Flags

**Never:**
- Create worktree without verifying it's ignored (project-local)
- Skip baseline test verification
- Proceed with failing tests without asking

## Integration

**Called by:**
- **brainstorming** - REQUIRED when design approved and implementation follows
- **subagent-driven-development** - REQUIRED before executing any tasks
- **executing-plans** - REQUIRED before executing any tasks

**Pairs with:**
- **finishing-a-development-branch** - REQUIRED for cleanup after work complete
