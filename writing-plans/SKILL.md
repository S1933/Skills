---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

Create an implementation plan that a capable engineer can execute without hidden repository or conversation context.

## Workflow

1. Read the approved specification and repository instructions. Map relevant architecture, conventions, commands, and existing tests before planning edits.
2. Resolve critical ambiguities. If the scope spans independent subsystems, split it into separately testable plans.
3. Define the file structure and interfaces first. State what each changed file owns and what later tasks consume from earlier tasks.
4. Divide work into vertical tasks that each produce an independently reviewable, testable result. Fold scaffolding and documentation into the task whose deliverable needs them.
5. For every task, include exact create/modify/test paths, constraints, interfaces, and small checkbox steps following RED, verify RED, GREEN, verify GREEN, REFACTOR, and commit.
6. Give exact commands and expected outcomes. Include concrete code or schema content where the implementer would otherwise have to invent the design.
7. Self-review for specification coverage, placeholders, inconsistent names/types, unsafe operations, dependency ordering, rollout, and rollback.
8. Save to the user’s requested location or `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`, then offer `subagent-driven-development` or `executing-plans` as explicit handoffs.

## Plan requirements

- Goal, architecture, stack, non-goals, and global constraints.
- Exact files and public interfaces.
- No `TBD`, “similar to above,” vague validation, or unspecified tests.
- Commands with expected RED/GREEN outcomes.
- Migration, compatibility, security, and generated-file handling where relevant.
- Completion criteria traceable to the specification.

The full document header, task template, examples, and handoff wording are in [full guidance](references/full-guidance.md).
