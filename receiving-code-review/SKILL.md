---
name: receiving-code-review
description: Use when review feedback must be understood, verified, prioritized, or challenged before implementation.
---

# Receiving Code Review

Treat review comments as technical claims to evaluate, not commands to obey or opportunities for performative agreement.

## Response pattern

1. Read the complete feedback and surrounding diff before editing.
2. Restate the requested behavior or concern in concrete terms.
3. Verify it against the repository, requirements, tests, and supported environments.
4. Ask a focused question when scope or intent remains ambiguous.
5. Decide: accept, adapt, defer with rationale, or push back with evidence.
6. Implement accepted items one at a time, starting with blockers and correctness/security issues.
7. Run relevant verification after each item and broader verification at the end.

## Source handling

For feedback from the user or project owner, prioritize clarifying intended behavior, but still surface contradictions or unsafe consequences. For external or automated reviewers, verify repository assumptions and version/API claims before changing code.

## Push back when

- The suggestion conflicts with requirements, architecture, compatibility, or established conventions.
- It adds unused abstraction, configuration, or “professional” machinery without a current need.
- It is technically incorrect for the versions or execution path in scope.
- It would weaken tests, security, data integrity, or failure handling.
- It expands the task beyond the authority the user provided.

Push back with paths, lines, command output, or primary documentation. State what alternative would satisfy the underlying concern.

## Communication

Do not use empty praise or claim agreement before verification. Acknowledge correct feedback by stating the concrete change and evidence. If your initial pushback was wrong, correct it plainly and continue.

## GitHub threads

Reply only after the corresponding change is implemented and verified, unless the response is a clarifying question or documented disagreement. Do not resolve another person’s thread without project permission.

Extended examples, common mistakes, and phrasing guidance are in [full guidance](references/full-guidance.md).
