---
name: jira
description: Use when a locally configured Jira CLI is required to inspect or mutate issues, comments, assignments, transitions, Tempo entries, or Confluence pages.
compatibility: Environment-specific; requires the locally configured private Jira CLI.
---

# Jira CLI

Use the local Jira CLI only against the user-configured private instance. Never expose instance URLs, usernames, account identifiers, tokens, issue content, or internal project details in public catalogue files or logs.

## Safety

- Prefer read-only commands while discovering issue state and available transitions.
- Confirm the exact issue, fields, transition, comment, worklog, or page before a mutation.
- Do not bulk-edit, transition, assign, comment, log time, or publish Confluence content unless the user explicitly requested that action.
- Never infer an account, project, sprint, or Tempo attribute when multiple matches exist.
- Show a concise mutation summary and verify the resulting state.

## Workflow

1. Check that the CLI and private configuration are available without printing secrets.
2. Resolve human-facing keys or names to stable internal identifiers through read-only commands.
3. Inspect current state, permissions, and valid transitions.
4. Present ambiguity when it could change the target or effect.
5. Execute the narrowest requested mutation.
6. Read the object again and report the verified result.

## Tempo and Confluence

For worklogs, resolve the issue’s internal task identifier and any requested account/work attribute dynamically; do not hardcode private identifiers. For Confluence, preserve existing page format and version semantics, and confirm before publishing destructive replacements.

The configured command catalogue, examples, field mappings, and troubleshooting notes are private and live in [full guidance](references/full-guidance.md). Load that reference only for the relevant operation.
