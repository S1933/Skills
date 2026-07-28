---
name: improve-codebase-architecture
description: Use when explicitly auditing a codebase for deep-module, seam, interface, or information-hiding opportunities in an architecture-focused visual report.
disable-model-invocation: true
compatibility: Requires repository read access and a local browser for the visual report.
---

# Improve Codebase Architecture

Find architecture opportunities where a deeper module can hide knowledge, simplify callers, and improve testability. Deliver a visual report, then explore the selected candidate with the user. Do not implement changes during the audit.

## Shared contracts

Run `repository-reconnaissance` before the audit. Apply the canonical [evidence standard](../references/evidence-standard.md) to every candidate and [execution safety](../references/execution-safety.md) to every command or external effect.

## Process

1. Load `codebase-design` vocabulary and use the reconnaissance map to select architecture, entry-point, high-change, test, and history evidence.
2. Trace duplicated orchestration, leaky vendor/storage concepts, broad change sets, shallow wrappers, unstable seams, and interfaces that expose lifecycle details.
3. Verify each candidate with file/line evidence and at least two callers or change paths. Reject cosmetic layering and speculative abstractions.
4. Produce a self-contained HTML report using [HTML-REPORT.md](HTML-REPORT.md). For each candidate show current shape, leaked knowledge, proposed deep module, interface sketch, migration path, tests that survive, impact, confidence, and effort.
5. Open or provide the local report without publishing it. Ask the user which candidate to explore.
6. Run `grilling` on the chosen candidate. Use `domain-modeling` when decisions change domain terminology, context boundaries, or ADR-worthy architecture.
7. Record the agreed design and hand off to planning only if the user requests implementation.

## Guardrails

- Do not call ordinary code cleanup an architecture improvement.
- Keep the HTML report local unless publication is separately requested.
- Do not propose implementation until the user selects and explores a candidate.

Detailed candidate heuristics, report examples, and the grilling loop are in [full guidance](references/full-guidance.md); its duplicated policy prose is non-canonical.
