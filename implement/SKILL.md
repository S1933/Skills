---
name: implement
description: Use when explicitly implementing work from an approved PRD, specification, or issue set.
disable-model-invocation: true
compatibility: Requires a client with repository editing, command execution, and subagent review support.
---

Implement the work described by the user in the PRD or issues.

Use the `test-driven-development` skill where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Before completion, use `verification-before-completion`, then
`requesting-code-review` to review the work.

Commit your work to the current branch.
