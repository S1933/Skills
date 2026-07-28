---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
---

# Systematic Debugging

Find the root cause before changing production behavior.

## Iron law

Do not propose or implement a fix until you can explain the causal chain from observed failure to root cause with evidence.

## Four phases

### 1. Root-cause investigation

Reproduce the failure reliably and capture the exact command, output, environment, and smallest failing scope. Read the complete error and stack trace. Inspect recent changes and trace bad values backward across component boundaries. Add temporary diagnostics only when they test a concrete question.

If reproduction is intermittent, gather observations and use condition-based waiting; do not substitute arbitrary sleeps. For multi-layer systems, log inputs and outputs at each boundary until the first divergence is located.

### 2. Pattern analysis

Find a nearby working example and compare it with the failure. List every difference, including configuration, data shape, ordering, versions, permissions, and timing. Check assumptions against source and documentation.

### 3. Hypothesis and test

State one falsifiable hypothesis: cause, mechanism, and expected observation. Change one variable or add one diagnostic. Run the smallest command that can disprove it. If disproved, return to the evidence and form a new hypothesis; do not stack speculative changes.

### 4. Implement and verify

Use `test-driven-development` to write the smallest regression test that demonstrates the root cause. Observe RED, make the minimal fix, observe GREEN, then run relevant broader verification. Remove temporary diagnostics and verify the original reproduction path.

## Escalation rule

After three failed fix attempts, stop editing and question the architecture, test premise, environment, or ownership boundary. Present the accumulated evidence and seek direction instead of attempting a fourth variation.

## Red flags

Stop when you are about to “try something,” alter several variables, skip reproduction, rely on a passing unrelated test, blame a dependency without tracing it, or explain away contradictory evidence.

Load detailed techniques only when needed: [root-cause tracing](root-cause-tracing.md), [defense in depth](defense-in-depth.md), [condition-based waiting](condition-based-waiting.md), and [polluter isolation](find-polluter.sh). Extended rationale and examples are in [full guidance](references/full-guidance.md).
