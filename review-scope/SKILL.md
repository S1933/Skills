---
name: review-scope
description: Use at the start of any code review to establish the base branch and gather the full set of changes to review — committed, staged, unstaged, and relevant untracked work. A building block that only scopes the diff — unlike /requesting-code-review (dispatches a reviewer subagent) and /receiving-code-review (how to respond to feedback you got).
---

# Review Scope

Establish exactly what to review before forming any judgment. Skipping this means reviewing a partial diff and missing regressions.

## 1. Determine the base branch

First existing wins: `develop` → `origin/develop` → `main` → `origin/main`.
Use `git show-ref --verify` to check each candidate; stop at the first that exists.

## 2. Inspect every layer of change

Run all of these — each surfaces a different slice of the work:

- `git status --short`
- `git diff --name-status`
- `git diff`
- `git diff --cached`
- `git diff <base>...HEAD`
- `git diff <base>...HEAD --stat`

## 3. Review all current work

Cover committed branch changes, staged changes, unstaged changes, and relevant untracked files when they appear in `git status`. A change is in scope regardless of which layer it lives in.
