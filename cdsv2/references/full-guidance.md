---
name: cdsv2
description: Use when authoring, reviewing, testing, troubleshooting, or migrating OVH CDSv2 workflow, action, worker-model, template, gate, matrix, service, or expression YAML.
compatibility: Environment-specific; runtime validation requires access to OVH CDSv2 and cdsctl.
---

# OVH CDSv2 CI/CD Skill

Use this skill for OVH CDSv2 YAML under `.cds/`. CDSv2 looks similar to GitHub Actions, but it has its own syntax, contexts, worker models, actions, and template rules.

## First Moves

1. Inspect the existing `.cds/` files before editing. Prefer local project patterns over generic CI/CD assumptions.
2. Keep changes scoped to the specific workflow, action, worker model, or template requested.
3. Validate with the repository's available commands, commonly `make lint`, `make lint-yaml`, `make lint-workflows`, and `make lint-shell`.
4. For behavior questions, load only the relevant reference file below.

## Critical Guardrails

### No CDS v1 Syntax

- Do not use `pipeline`, `application`, `environment`, or job-level `requirements`.
- Use flat workflow files under `.cds/workflows/`.

### No GitHub Actions Confusion

- Worker models: use `library/default-container`, `library/node-22`, etc.; never `ubuntu-latest`.
- Actions: use `actions/uploadArtifact`, `actions/downloadArtifact`, and `actions/checkout`; do not use GitHub action names like `upload-artifact` or `actions/checkout@v3`.
- Contexts: use `${{ cds.* }}`, `${{ git.* }}`, `${{ vars.* }}`, `${{ steps.* }}`, `${{ jobs.* }}`; never `${{ github.* }}` or `${{ secrets.* }}`.
- Outputs: use `worker export name value`; never write to `$GITHUB_OUTPUT`.
- Worker CLI in a v2 job: only `worker output <name> <value>` (alias `export`) and `worker result add` exist. `worker tag`, `worker upload`, `worker download`, `worker cache`, `worker key`, and `worker tmpl` are v1-only — use the matching built-in action (`actions/uploadArtifact`, `actions/cache`, `actions/keyInstall`, …) instead.
- Templates: use Go template delimiters `[[ ... ]]`, not `${{ ... }}` for template-time interpolation.
- Triggers: `pull-request` types are `opened`, `reopened`, `closed`, `edited` — there is no `synchronize` (a GitHub Actions type). A re-push to a PR branch fires a `push` event, not a PR event.

### Bash Preamble

Multi-line bash `run:` blocks must start with:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
```

For a single command, prefer a one-line `run: <command>` without the preamble.

Use `printf "[INFO] %s\n" "message"` and `printf "[ERROR] %s\n" "message"` for logs, quote expansions, and use lowercase local variables in bash. See [Conventions > Bash Script Conventions](conventions.md#bash-script-conventions).

## Reference Map

Read the smallest reference that matches the task:

- [Core Syntax](core-syntax.md): workflow structure, triggers, steps, built-in actions, contexts, expressions, variables, integrations, semver, gates, matrix, services, external workflows, and a complete pipeline example.
- [Actions, Models & Templates](actions-models-templates.md): custom actions, action outputs, post hooks, worker model definitions, workflow template authoring, template escaping, helper functions, and contrib actions.
- [Workflow Patterns](workflow-patterns.md): advanced triggers, path/glob behavior, gates, dynamic matrices, concurrency, conditionals, job outputs, changesets, notifications, and permissions.
- [Runtime & Infrastructure](runtime.md): worker model options, VM flavors, regions, services, integration usage, caching, semver sources, staging deployment, and troubleshooting.
- [Conventions & Style](conventions.md): YAML style, bash conventions, naming, skip markers, boolean rules, and cross-repository references.

## Directory Structure

| Type | Path |
|------|------|
| Workflows | `.cds/workflows/<name>.yaml` |
| Actions | `.cds/actions/<name>.yaml` |
| Worker Models | `.cds/worker-models/<name>.yaml` |
| Workflow Templates | `.cds/workflow-templates/<name>.yaml` |

## Naming Rules

| Element | Convention | Examples |
|---------|------------|----------|
| Step IDs | PascalCase | `Requirements`, `Install`, `BuildArtifacts` |
| Action inputs | kebab-case | `auto-detect`, `node-version` |
| Template parameters | snake_case | `node_version_worker`, `deploy_region` |
| Job names | kebab-case | `lint-test`, `build-deploy` |
| Environment variables | UPPER_SNAKE_CASE | `DOCKER_REGISTRY_URL`, `CDS_RUN_NUMBER` |

Keep action `inputs:`, gate inputs, and template parameters in alphabetical order when adding new entries. For the full naming table, see [Conventions > Naming](conventions.md#naming-conventions-complete).

## Minimal Workflow Pattern

```yaml
name: my-workflow
on: [push, pull-request]

jobs:
  checks:
    runs-on: library/node-22
    steps:
      - uses: actions/checkout
      - id: Test
        run: |-
          #!/usr/bin/env bash
          set -Eeuo pipefail
          make test
```

For full workflow keys and trigger variants, see [Core Syntax > Workflow Structure](core-syntax.md#workflow-structure) and [Core Syntax > Triggers](core-syntax.md#triggers-on).

## Common Authoring Patterns

### Action Requirement Step

```yaml
runs:
  steps:
    - id: Requirements
      run: |-
        #!/usr/bin/env bash
        set -Eeuo pipefail
        if command -v pnpm >/dev/null 2>&1; then
          worker export should-install "false"
        else
          worker export should-install "true"
        fi

    - id: Install
      if: ${{ steps.Requirements.outputs.should-install == 'true' }}
      run: |-
        #!/usr/bin/env bash
        set -Eeuo pipefail
        npm install -g pnpm@${{ inputs.version }}
```

For full custom action syntax, see [Actions, Models & Templates > Custom Actions](actions-models-templates.md#custom-actions-cdsactionsyaml).

### Variable Export

```text
- id: Build
  run: |-
    #!/usr/bin/env bash
    set -Eeuo pipefail
    worker export version "1.2.3"

# Same job:
${{ steps.Build.outputs.version }}

# Different job:
${{ jobs.build.outputs.version }}
```

`worker export` values are strings. Compare them with string literals in CDS expressions.

### Boolean Conditions

- Gate boolean inputs are real booleans: use `if: ${{ gate.approve }}`.
- `worker export` step outputs are strings: use `if: ${{ steps.Check.outputs.should-run == 'true' }}`.
- Action inputs preserve YAML types in expressions: quote boolean-like defaults and caller values when you plan to use string comparisons.
- Avoid `!` on step outputs and string-like inputs; use explicit comparisons.

See [Conventions > Boolean Conditions Reference](conventions.md#boolean-conditions-reference).

### Makefile Preference

When existing project conventions allow it, prefer Makefile targets and fall back to package-manager commands:

```bash
if [ -f Makefile ]; then make install; else pnpm install; fi
if [ -f Makefile ]; then make build; else pnpm build; fi
if [ -f Makefile ]; then make test; else pnpm test; fi
```

## Template Essentials

Workflow templates use `[[ ... ]]` for template-time interpolation:

```yaml
name: my-template
parameters:
  - key: node_version_worker
    default: ".cds/worker-models/node-22.yaml"

spec: |-
  name: [[ .cds.workflow ]]
  jobs:
    build:
      runs-on: [[ .params.node_version_worker ]]
      steps:
        - uses: actions/checkout
```

For conditionals, helper functions, escaped bash `[[ ]]`, and consumer usage, see [Actions, Models & Templates > Workflow Templates](actions-models-templates.md#workflow-templates-cdsworkflow-templatesyaml).

## Validation Notes

- Lint YAML with the repo's `yamllint` configuration.
- Lint CDS workflows with `cdsctl X workflow lint .cds/workflows/` when available.
- Lint embedded bash with the repo's shellcheck/yq extraction when available.
- Preserve existing YAML indentation exactly when editing nested blocks or template `spec:` content.
