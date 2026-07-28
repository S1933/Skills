---
name: finishing-a-development-branch
description: Use when implementation and verification are complete and the branch needs an explicit merge, pull-request, retention, or cleanup decision.
compatibility: Requires Git; pull-request options require a configured repository host integration.
---

# Finishing a Development Branch

Verify the branch, establish its base and workspace context, then let the user choose how to integrate or retain it.

## Process

1. Run the repository’s relevant full verification from the feature workspace. Stop on failure; do not present integration options for unverified work.
2. Inspect current branch, status, worktree location, and whether the environment is client-managed. Preserve unrelated user changes.
3. Determine the base branch from repository context and merge-base evidence. Do not guess when branches are ambiguous.
4. Summarize commits, verification, and any remaining risks. Present exactly the applicable choices: merge locally, push and open a pull request, keep the branch/worktree, or discard it.
5. Wait for the user’s choice before mutating branch, remote, or worktree state.
6. Execute only that choice. For a merge, merge first and verify the merged result before cleanup. For a PR, push only the selected branch and create the requested PR. For retention, leave state unchanged.
7. Cleanup a worktree or delete a branch only after successful integration or explicit discard confirmation, and only from a safe checkout outside the target worktree.

## Guardrails

- Never push, merge, delete, or remove a worktree implicitly.
- Never delete a branch before its integration result is verified.
- Never force-push or rewrite history unless separately requested and confirmed.
- Never use destructive reset or clean operations to finish a branch.
- Report what remains recoverable after any approved cleanup.

Exact command sequences, environment detection, PR formatting, and cleanup cases are in [full guidance](references/full-guidance.md).
