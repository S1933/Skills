---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
compatibility: Requires a client with subagent support and Bash.
---

# Subagent-Driven Development

Execute a reviewed implementation plan by giving each independent task to a fresh implementer, then passing the result through specification and quality gates before moving on.

## Preconditions

- Work on an isolated branch or workspace established with `using-git-worktrees`.
- Review the whole plan for missing interfaces, dependency order, and unsafe operations.
- Record the base commit. Never derive a multi-commit review range with `HEAD~1`.
- Keep tasks independent; use inline execution when tasks require tightly shared state.

## Per-task loop

1. Create a self-contained task brief with exact files, constraints, interfaces, tests, and relevant plan text.
2. Dispatch one fresh implementer. The implementer follows `test-driven-development`, verifies its work, and reports status honestly.
3. If the implementer reports blocked or needs clarification, resolve the cause before continuing. Do not reinterpret a blocked result as done.
4. Generate the review package with `scripts/review-package BASE HEAD`, using the recorded task base and the printed output path.
5. Dispatch a specification reviewer. It checks only whether the task matches requirements and whether required behavior is missing or extra.
6. After specification approval, dispatch a quality reviewer using the same immutable review package.
7. Resolve every blocking item. Verify warning items yourself and record the disposition; do not silently discard them.
8. Run the task’s verification commands and record durable progress before starting the next task.

## Isolation and handoffs

Subagents receive only explicit files or review packages; do not assume conversation context transfers. Reviewers are read-only. Implementers may edit only the assigned workspace and must not push, rewrite history, or alter unrelated user changes.

## Completion

After all task gates pass, run repository-wide verification and a final integration review. Then use `finishing-a-development-branch` to present merge, PR, retention, or cleanup options. Never claim completion from subagent summaries alone.

## Stop conditions

Stop for ambiguous requirements, overlapping tasks, repeated verification failures, a dirty workspace that cannot be isolated, review packages that do not match the intended base/head, or any request for authority outside the user-approved scope.

Detailed status handling, prompt construction, model selection, examples, and recovery procedures are in [full guidance](references/full-guidance.md). Prompt templates remain in [implementer-prompt.md](implementer-prompt.md) and [task-reviewer-prompt.md](task-reviewer-prompt.md).
