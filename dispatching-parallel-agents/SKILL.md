---
name: dispatching-parallel-agents
description: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies
compatibility: Requires a client with parallel subagent support.
---

# Dispatching Parallel Agents

Parallelize independent investigations or changes while keeping ownership and integration explicit.

## Decision gate

Use parallel agents only when tasks have separate files or read-only scopes, no required result ordering, and no shared mutable state. Use sequential work when one result informs another, agents would edit the same area, or integration risk exceeds the latency saved.

## Pattern

1. Partition the work into independent domains with clear boundaries.
2. Give each agent one objective, exact scope, constraints, expected evidence, verification commands, and prohibited mutations.
3. Dispatch all agents together. Do not make one agent responsible for coordinating hidden dependencies.
4. Review every result yourself. Re-open cited evidence and reject unsupported conclusions.
5. Detect overlapping edits or contradictory assumptions before integration.
6. Integrate deliberately, then run combined verification across the whole result.

## Prompt contract

Each prompt states the problem, owned files or audit dimension, relevant context, output format, completion criteria, and whether edits are allowed. Require agents to report uncertainty and unaudited scope.

## Stop conditions

Stop parallel dispatch when scopes overlap, a shared prerequisite changes, agents need the same mutable environment, or a result changes the assumptions of outstanding tasks.

Examples, prompt templates, common mistakes, and comparison cases are in [full guidance](references/full-guidance.md).
