---
name: using-git-worktrees
description: Use when implementation work needs an isolated Git workspace or when an execution workflow requires isolation before changes begin.
compatibility: Requires Git worktree support or an equivalent client-native isolation mechanism.
---

# Using Git Worktrees

Create or verify an isolated workspace before implementation without disturbing the user’s current checkout.

## Workflow

1. Detect whether the current workspace is already an isolated worktree or client-managed equivalent. Do not create nested isolation unnecessarily; a submodule is not a worktree.
2. Prefer the client’s native worktree mechanism when available. Otherwise inspect repository instructions for a preferred location, then use a conventional ignored directory such as `.worktrees/`.
3. Before creating a repository-local worktree, verify the parent directory is ignored with `git check-ignore`. If it is not ignored, stop and resolve that safety issue before proceeding.
4. Choose a new branch name that describes the task. Never reuse or overwrite an existing branch or path without explicit direction.
5. Create the worktree with Git, change into it, and confirm repository root, branch, and clean status.
6. Run only the project setup commands implied by existing lockfiles and instructions. Do not upgrade or install unrelated dependencies.
7. Run the project’s baseline verification. If it fails, report the exact failure and ask whether to continue; do not attribute pre-existing failures to later work.
8. Report the isolated path, branch, and baseline result.

## Guardrails

- Never start implementation on `main` or `master` without explicit consent.
- Preserve dirty user changes in the original checkout.
- Do not guess a worktree location when repository conventions exist.
- Do not remove a worktree or branch as part of setup.
- Do not use destructive cleanup to make the baseline appear clean.

Platform-specific detection commands, setup examples, fallback selection, and troubleshooting are in [full guidance](references/full-guidance.md).
