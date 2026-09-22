---
name: cdsv2
description: Use when authoring, reviewing, testing, troubleshooting, or migrating OVH CDSv2 workflow, action, worker-model, template, gate, matrix, service, or expression YAML.
compatibility: Environment-specific; runtime validation requires access to OVH CDSv2 and cdsctl.
---

# OVH CDSv2 CI/CD

Author CDSv2 configuration using repository conventions and the v2 schema. Do not mix CDS v1 or GitHub Actions syntax into CDSv2 YAML.

## First moves

1. Read the repository’s `.cds/` tree and nearest working workflow/action/template.
2. Identify whether the task concerns syntax, expressions, runtime behavior, worker models, templates, gates, matrices, services, or migration.
3. Load only the matching reference below.
4. Preserve local naming, requirement, and Makefile conventions.
5. Validate YAML and available CDSv2 schema/runtime behavior without exposing private instance details.

## Critical guardrails

- Use CDSv2 v2 objects and expressions only.
- Do not translate GitHub Actions keys mechanically.
- Shell steps use the required strict Bash preamble and quote expressions safely.
- Export values according to same-job versus cross-job scope.
- Keep boolean conditions boolean; avoid stringly typed comparisons.
- Prefer existing Makefile targets for project commands.
- Never publish hostnames, tokens, worker credentials, account names, or internal project paths.

## Reference routing

- Core YAML and expressions: [core syntax](references/core-syntax.md)
- Workflow/jobs/gates/matrices: [workflow patterns](references/workflow-patterns.md)
- Runtime, services, and exports: [runtime](references/runtime.md)
- Actions, worker models, and templates: [actions, models, templates](references/actions-models-templates.md)
- Naming and repository style: [conventions](references/conventions.md)
- Historical examples and complete checklist: [full guidance](references/full-guidance.md)

If runtime validation needs the private CDSv2 instance and access is unavailable, perform static validation and report the unverified scope.
