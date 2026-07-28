---
name: codebase-design
description: Use when designing or improving module interfaces, seams, information hiding, testability, navigability, or deep-module boundaries.
---

# Codebase Design

Use a shared vocabulary to make modules deeper: simpler interfaces that hide more implementation knowledge.

## Core vocabulary

- **Module:** a unit that owns a meaningful design decision.
- **Interface:** what callers must know.
- **Depth:** useful capability divided by interface complexity.
- **Seam:** a stable point where implementations can vary.
- **Adapter:** translation that keeps external concepts out of the domain.
- **Leverage:** how much behavior one decision or interface controls.
- **Locality:** keeping knowledge and changes near their owner.

## Design tests

Ask whether callers can use the module without knowing storage, vendor, transport, sequencing, or lifecycle details. Prefer one coherent operation over many orchestration steps. Treat the public interface as the test surface; test behavior through it and keep internals free to change.

A proposed seam becomes credible when at least two real implementations need it. Avoid speculative abstractions with one hypothetical consumer. Use the deletion test: if an implementation disappears, callers should change little or not at all.

## Method

1. Identify knowledge leaking across files or layers.
2. Name the owner of that knowledge.
3. Design at least two materially different interfaces.
4. Compare caller burden, hidden complexity, testability, failure semantics, and likely change paths.
5. Choose the deepest interface that matches current evidence, then define migration steps.

Extended examples, relationships, rejected framings, and design-it-twice guidance are in [full guidance](references/full-guidance.md), [DEEPENING.md](DEEPENING.md), and [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md).
