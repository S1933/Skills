---
name: improve
description: Use when surveying a codebase for prioritized improvement opportunities across correctness, security, performance, testing, maintainability, developer experience, migrations, or product direction.
compatibility: Requires repository read access; parallel subagent support is recommended.
---

# Improve

Survey a codebase as a senior advisor and produce prioritized, self-contained implementation plans for other agents. Do not implement the findings.

## Shared contracts

Run `repository-reconnaissance` before the audit. Apply the canonical [evidence standard](../references/evidence-standard.md) to every finding and [execution safety](../references/execution-safety.md) to every command or external effect.

## Audit-specific rules

- Produce recommendations and plans, not implementation changes.
- Ask the user to select findings when the choice materially changes plan scope.
- Run execution or issue-publication variants only when explicitly requested.

## Workflow

### 1. Reconnaissance

Use the reconnaissance map to bound the audit and load [audit playbook](references/audit-playbook.md) for dimension-specific routing.

### 2. Parallel audit

Inspect correctness, security, performance, testing, maintainability, developer experience, architecture, migrations, and product opportunities. Parallelize independent dimensions when subagents are available, but give each a bounded scope and require file/line evidence.

### 3. Vet and prioritize

Re-open cited locations, reject duplicates and unsupported claims, and account for existing conventions. Rank opportunities by impact, urgency, confidence, blast radius, effort, and dependency order. Ask the user to confirm which opportunities should become plans when selection is material.

### 4. Write implementation plans

Use [plan template](references/plan-template.md). Each plan must be independently executable: goal, evidence, exact files, constraints, bite-sized TDD steps, commands with expected outcomes, migration/rollback concerns, and completion criteria. Link related plans and identify prerequisite order.

## Invocation variants

Narrow scope when the user names a subsystem or concern. For a broad request, cover all dimensions but explicitly report sampling. In repeat mode, re-check previous findings rather than copying them forward.

## Completion

Provide the prioritized index and paths to written plans. Do not claim a problem is fixed; this skill produces verified recommendations. Follow [closing the loop](references/closing-the-loop.md) when implementation results return.

Historical rationale and examples remain in [full guidance](references/full-guidance.md); its duplicated policy prose is non-canonical.
