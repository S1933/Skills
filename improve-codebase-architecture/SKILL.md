---
name: improve-codebase-architecture
description: Use when explicitly auditing a codebase for deep-module, seam, interface, or information-hiding opportunities in an architecture-focused visual report.
disable-model-invocation: true
compatibility: Requires repository read access and a local browser for the visual report.
---

# Improve Codebase Architecture

Find architecture opportunities where a deeper module can hide knowledge, simplify callers, and improve testability. Deliver a visual report, then explore the selected candidate with the user. Do not implement changes during the audit.

## Process

1. Load `codebase-design` vocabulary and inspect repository instructions, architecture, entry points, high-change paths, tests, and history.
2. Trace duplicated orchestration, leaky vendor/storage concepts, broad change sets, shallow wrappers, unstable seams, and interfaces that expose lifecycle details.
3. Verify each candidate with file/line evidence and at least two callers or change paths. Reject cosmetic layering and speculative abstractions.
4. Produce a self-contained HTML report using [HTML-REPORT.md](HTML-REPORT.md). For each candidate show current shape, leaked knowledge, proposed deep module, interface sketch, migration path, tests that survive, impact, confidence, and effort.
5. Open or provide the local report without publishing it. Ask the user which candidate to explore.
6. Run `grilling` on the chosen candidate. Use `domain-modeling` when decisions change domain terminology, context boundaries, or ADR-worthy architecture.
7. Record the agreed design and hand off to planning only if the user requests implementation.

## Guardrails

- Read-only except for the requested local report/design document.
- Never reproduce secrets or private environment details.
- Distinguish observation from inference and state unaudited scope.
- Do not call ordinary code cleanup an architecture improvement.

Detailed candidate heuristics, report examples, and the grilling loop are in [full guidance](references/full-guidance.md).
