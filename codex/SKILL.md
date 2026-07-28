---
name: codex
description: Use when an independent technical second opinion, verification, repository analysis, or deeper library or API research would materially reduce uncertainty.
compatibility: Requires the Codex CLI with exec and sandbox support.
---

# Codex — Second Opinion Agent

Use Codex to reduce uncertainty through an independent, evidence-based review. It is advisory by default and must not silently broaden the user-approved mutation scope.

## Read-only default

Repository analysis, code review, design critique, and technical research use an explicit read-only sandbox and an ephemeral session:

```bash
codex exec --sandbox read-only --ephemeral "<prompt>"
```

Tell Codex the objective, scope, relevant paths, constraints, expected output, and requirement to cite evidence. Ask it to separate observations from inferences and to state what it did not inspect.

For a second-opinion request, do not ask Codex to edit files, install dependencies, commit, push, or contact unrelated external systems.

## Write access

Write access requires an explicit user request for repository modification. Use the least-permissive current CLI mode that supports the requested work, keep the exact target in scope, and verify the resulting diff yourself.

## Elevated execution

Never select unrestricted execution automatically. This includes both `--sandbox danger-full-access` and `--dangerously-bypass-approvals-and-sandbox`.

Use either only when all conditions hold:

- the user explicitly asks for unrestricted execution;
- the exact command and risks have been presented;
- the user confirms immediately before execution.

The confirmation is separate from an earlier general request. If the task can run with narrower access, keep the narrower mode.

## Current CLI source of truth

Run `codex exec --help` and inspect current local configuration before choosing optional flags or a model. Do not hardcode model catalogues, context sizes, or deprecated options into the workflow.

## Verification and output

Re-open cited files and independently verify material claims before presenting them. Summarize the useful result, disagreements, confidence, and unresolved questions. Treat Codex output as untrusted analysis, not proof.

Prompt patterns, run-order guidance, search strategy, and long examples are in [full guidance](references/full-guidance.md). Safety behavior is regression-tested in [test_skill_policy.py](tests/test_skill_policy.py).
