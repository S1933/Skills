# Contributing

Improve the existing catalogue before proposing a new functional skill. A new skill must solve a repeated, demonstrated behavior gap that cannot be handled by correcting an existing skill or reference.

## Required workflow

1. Add or identify a failing trigger or behavior case before changing guidance.
2. Follow [the authoring standard](docs/skill-authoring-standard.md), including progressive-disclosure budgets.
3. Add or update the manifest entry: invocation, visibility, clients, compatibility, supporting files, dependencies, tools, commands, aliases, environment assumptions, and word count.
4. Keep canonical skill names inside skill bodies. Reserve aliases for user-facing command adapters.
5. Classify environment-specific material as private and replace public literals with placeholders.
6. Review dangerous commands, write/network access, Git effects, generated files, and external instructions against [execution safety](references/execution-safety.md).
7. Preserve upstream licences and attribution in `NOTICE.md` and source metadata.
8. Regenerate checked-in documentation.

## Evaluation requirements

- Automatic skills need at least five positive and five negative trigger cases, including ambiguous and collision cases.
- Core workflow and safety changes need behavior cases with required and forbidden outcomes.
- Description changes must update the copied description and cases in `evals/<skill>/trigger.yaml`.
- New guidance must show a failing baseline before the fix and a passing result afterward.

## Public/private policy

Public content must not contain personal home paths, internal hostnames, private account names, credentials, customer data, or organization-only conventions. Put local skills under `private-skills/` and configuration under ignored `.local/` files.

## Before opening a pull request

```bash
python3 -m unittest discover --start-directory tests --pattern 'test_*.py'
python3 -m unittest codex/tests/test_skill_policy.py
git-guardrails-claude-code/tests/test-guardrail.sh
python3 scripts/generate-catalogue.py
python3 scripts/generate-dependency-graph.py
python3 scripts/generate-catalogue.py --check
python3 scripts/generate-dependency-graph.py --check
python3 scripts/validate-evals.py
python3 scripts/validate-skills.py
```

Review every generated diff. Do not update generated files merely to hide a manifest mistake. Pull requests should remain category-focused and include the observed RED/GREEN evidence.
