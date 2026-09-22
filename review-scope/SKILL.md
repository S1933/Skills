---
name: review-scope
description: Use when beginning a code review that must include committed, staged, unstaged, and relevant untracked changes against the correct base.
compatibility: Requires Git repository access.
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
