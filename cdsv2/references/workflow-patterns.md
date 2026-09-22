# CDSv2 Workflow Patterns Reference

Patterns for workflow orchestration and control flow: triggers, gates, matrix, concurrency, conditionals, outputs, changesets, notifications, and permissions.

## Contents
- [Additional Expression Patterns](#additional-expression-patterns)
- [Glob Pattern Reference](#glob-pattern-reference)
- [Additional Triggers](#additional-triggers)
- [Gate Patterns](#gate-patterns)
- [Matrix Patterns](#matrix-patterns)
- [Concurrency Patterns](#concurrency-patterns)
- [Conditional Patterns](#conditional-patterns)
- [Output Patterns](#output-patterns)
- [Changeset Workflow](#changeset-workflow)
- [Notifications](#notifications)
- [AsCode Permissions](#ascode-permissions)

For trigger syntax (push/PR/schedule/workflow-run), see [Core Syntax > Triggers](core-syntax.md#triggers-on).

## Additional Expression Patterns

For the full expression functions reference, see [Core Syntax > Expression Syntax](core-syntax.md#expression-syntax-).

### Advanced `hashFiles` Patterns

```text
# Exclusion patterns in hashFiles
${{ hashFiles('**/*.go', '!**/vendor/**') }}
${{ hashFiles('**/package-lock.json') }}

# Multiple lock files
${{ hashFiles('go.sum', 'go.mod') }}
```

### Result Function (Artifact Metadata)

```yaml
# Access artifact metadata after upload
${{ result('generic', 'my-artifact.tar.gz').md5 }}
${{ result('generic', '*.txt').sha256 }}
${{ result('docker', 'my-image:latest').digest }}
${{ result('helm', 'my-chart').version }}

# Supported artifact types: conan, coverage, debian, deployment, docker,
#   generic, gradle, helm, maven, npm, nuget, puppet, python, release,
#   sbt, staticFiles, terraformProvider, terraformModule, tests, variable
```

## Glob Pattern Reference

```yaml
# Single wildcard (any chars except /)
path: '*.txt'           # matches file.txt
path: 'src/*.go'        # matches src/main.go

# Single char wildcard
path: 'file?.txt'       # matches file1.txt, fileA.txt

# Character class
path: '[abc]*.txt'      # matches a.txt, b1.txt

# Globstar (recursive)
path: '**/*.txt'        # matches any .txt in any directory
path: 'src/**'          # matches everything under src/

# Exclusions
path: |
  src/**
  !src/**/*.test.go
  !**/vendor/**

# Multiple patterns (newline, space, or comma)
path: 'src/** tests/** !**/*.md'
```

## Additional Triggers

For the core trigger syntax (push, pull-request, schedule, workflow-run), see [Core Syntax > Triggers](core-syntax.md#triggers-on).

```yaml
# Workflow/model update triggers
on:
  workflow-update:  # When workflow file changes
  model-update:     # When worker model changes

# Pull request comment trigger
  pull-request-comment:
    types: [created]
    branches: [main, develop]
    paths: ["src/**"]
    comment: "/deploy"
    # SECURITY: PR comment runs with base branch context, not PR author permissions

# Push with commit message filter
  push:
    commit: "\\[release\\]"    # Regex on commit message

# Webhook triggers
  repository-webhook:         # Project repository webhook
    model-update:
    # HMAC signature verification via X-Hub-Signature header

  workflow-webhook:           # Project workflow webhook

# Access webhook payload in steps:
#   echo "${{ cds.event.my_key }}"
```

## Gate Patterns

For basic gate syntax, see [Core Syntax > Gates](core-syntax.md#gates-manual-approval).

### Simple Manual Gate

```yaml
gates:
  manual:
    if: "${{ success() && gate.manual }}"

jobs:
  deploy:
    gate: manual
    steps:
      - run: ./deploy.sh
```

### Branch-Conditional Gate

```yaml
gates:
  prod-gate:
    if: "${{ git.ref_name == 'main' && gate.approve && success() }}"
    inputs:
      approve:
        type: boolean
    reviewers:
      groups: [sre-team, devops]
      users: [lead-developer]
```

### Gate with Text Input

```yaml
gates:
  deploy-gate:
    if: "${{ success() && gate.manual }}"
    inputs:
      version:
        type: text
        description: "Version to deploy"
      environment:
        type: text
        description: "Target environment"

jobs:
  deploy:
    gate: deploy-gate
    steps:
      - run: |
          echo "Deploying version ${{ gate.version }} to ${{ gate.environment }}"
```

### Gate with Choice Input

```yaml
gates:
  deploy-gate:
    if: "${{ success() && gate.manual }}"
    inputs:
      zone:
        type: choice
        default: zoneA
        options:
          multiple: false
          values: [zoneA, zoneB, zoneC]
      approve:
        type: boolean

jobs:
  deploy:
    gate: deploy-gate
    steps:
      - run: echo "Deploying to ${{ gate.zone }}"
```

> `choice` is not a real input type — the dropdown and validation come entirely from the `options:` block (`values:` + `multiple:`). The `type:` itself only meaningfully distinguishes `boolean` and `number` (everything else is a string). Set `multiple: true` for a multi-select (the value becomes a list).

## Matrix Patterns

For static matrix and dynamic matrix from job output syntax, see [Core Syntax > Matrix Strategy](core-syntax.md#matrix-strategy).

**Matrix limits:** CDS matrices support only the axis map — there is no `include`/`exclude`, `max-parallel`, or `fail-fast`, and no cap on combinations (an N×M×… product is generated as-is). Axis expansion order is not stable. Outputs from all permutations are merged into one flat `jobs.<id>.outputs` map (last writer wins on key collision).

### Matrix with Named Jobs

```yaml
jobs:
  build:
    name: "Build ${{ matrix.component }}"
    strategy:
      matrix:
        component: [frontend, backend, worker]
    runs-on: library/default-container
    steps:
      - run: make build-${{ matrix.component }}
```

## Concurrency Patterns

For settings, `order` semantics, and the workflow-vs-project scope distinction, see [Core Syntax > Concurrency Control](core-syntax.md#concurrency-control).

### Per-Branch Concurrency (Dynamic Naming)

A CDS expression in the rule's `name` produces one queue per resolved value:

```yaml
concurrency: ${{ format('deploy-{0}', git.ref_name) }}
concurrencies:
  - name: ${{ format('deploy-{0}', git.ref_name) }}
    pool: 1
    cancel-in-progress: true
```

`main` and `develop` deploy in parallel; two pushes to `main` serialize.

### Job-Level Concurrency

Job-level concurrency serializes a specific job across runs of the **same workflow**:

```yaml
concurrencies:
  - name: deploy-rule
    pool: 1
jobs:
  deploy:
    concurrency: deploy-rule
    runs-on: library/default-container
    steps:
      - run: ./deploy.sh
```

The slot is held while the job runs and released the moment it ends — sibling and downstream jobs in the same run are not protected. To lock the entire run end-to-end (including manual gates and prod chains), put the concurrency at the **workflow** level, not the job.

### Cross-Workflow Serialization (Project-Level Rules)

To make multiple distinct workflows share one queue, the rule **must be defined at project level** and referenced by name. A `concurrencies:` block inside a workflow file is workflow-scoped; declaring the same name in two different files yields two separate queues.

```yaml
# At project level (as-code or UI): rule "shared-deploy" with pool: 1.

# Each consumer workflow:
name: workflow-a
concurrency: shared-deploy
# (no concurrencies: block — the rule lives at project scope)
```

### Workflow Templates and Concurrency

**Verified behavior:** workflow-level `concurrency:` / `concurrencies:` declared inside a template's `spec` is **silently ignored**. Templates contribute jobs (and gates) to the consumer workflow; top-level workflow metadata is not propagated.

What does work from inside a template:

- **Job-level `concurrency:`** on the template's jobs — slot is held only while that specific job runs, so this serializes individual jobs but does not lock an entire chain.

What must be done in the consumer workflow:

- **Workflow-level `concurrency:`** for "lock the entire run" semantics (including manual gates and downstream jobs).
- **Project-level rule + reference** for cross-workflow serialization across multiple consumers of the same template.

```yaml
# Template — only job-level concurrency takes effect here:
spec: |-
  jobs:
    deploy-prod-[[$.params.region]]:
      concurrency: deploy-prod-[[$.params.region]]
      ...

# Consumer workflow — declare workflow-level concurrency yourself:
name: my-app-deploy
from: PROJECT/vcs/repo/deploy-application-template@master
parameters:
  region: eu
concurrency: deploy-eu
concurrencies:
  - name: deploy-eu
    pool: 1
    order: oldest_first
```

### Same Rule on Workflow + Job (Deadlock)

Don't apply the same `pool: 1` rule at both workflow and job level:

```yaml
concurrencies:
  - name: rule1
concurrency: rule1
jobs:
  build:
    concurrency: rule1
```

The workflow takes the only slot when it starts; the job then waits for a slot the workflow itself is holding. The run never completes.

### FIFO Release Timeline (Job-Level)

With `pool: 1` and `order: oldest_first`, blocked jobs are released in arrival order across runs:

```yaml
concurrencies:
  - name: rule1
    pool: 1
jobs:
  build:
    concurrency: rule1
    steps: [{ run: sleep 20 }]
  package:
    needs: [build]
    concurrency: rule1
    steps: [{ run: sleep 20 }]
```

Triggered twice in quick succession, the execution order is:

1. run #1 `build`
2. run #2 `build` (queued — pool full while #1 runs)
3. run #1 `package` (queued behind #2's `build` because `build` entered the queue first)
4. run #2 `package`

The slot releases per job, not per run. If run #1 must finish entirely before run #2 starts, use **workflow-level** concurrency instead — never combine the same rule at both levels.

## Conditional Patterns

**Default condition:** a job/step with no `if:` runs as `${{ success() }}`. At step scope `success()` treats a `Skipped` step as success; at **job/needs scope** a `Skipped` upstream makes `success()` false — so a job downstream of a skipped job is itself skipped. To run anyway, use `if: always()` or test `needs.<job>.result` explicitly.

### Branch-Based Conditions

```yaml
jobs:
  deploy-staging:
    if: "${{ git.ref_name == 'develop' && success() }}"

  deploy-prod:
    if: "${{ git.ref_name == 'main' && success() }}"

  deploy-feature:
    if: "${{ startsWith(git.ref_name, 'feature/') && success() }}"
```

### Tag-Based Conditions

```yaml
jobs:
  release:
    if: "${{ git.ref_type == 'tag' && startsWith(git.ref_name, 'v') }}"
```

### PR-Based Conditions

```yaml
jobs:
  pr-check:
    if: "${{ cds.event_name == 'pull-request' }}"
```

### Failure Handling

```yaml
jobs:
  test:
    runs-on: library/default-container
    steps:
      - run: ./run-tests.sh

  notify-failure:
    needs: [test]
    if: "${{ failure() }}"
    runs-on: library/default-container
    steps:
      - run: ./send-notification.sh "Tests failed"

  cleanup:
    needs: [test]
    if: "${{ always() }}"
    runs-on: library/default-container
    steps:
      - run: ./cleanup.sh
```

## Output Patterns

### Chaining Job Outputs

```yaml
jobs:
  version:
    runs-on: library/default-container
    steps:
      - id: Calc
        run: |-
          #!/usr/bin/env bash
          set -Eeuo pipefail
          VERSION=$(cat version.txt)
          worker export version "${VERSION}"
    outputs:
      version:
        value: ${{ steps.Calc.outputs.version }}

  build:
    needs: [version]
    runs-on: library/default-container
    steps:
      - run: make build VERSION=${{ jobs.version.outputs.version }}

  deploy:
    needs: [build, version]
    runs-on: library/default-container
    steps:
      - run: ./deploy.sh ${{ jobs.version.outputs.version }}
```

## Changeset Workflow

Standard pipeline for libraries using changesets.

**Conventions:**
- **Branch Protection:** Only `changeset-release/master` merges to `master`
- **Concurrency:** Use named groups (`should_open_pr`) with `oldest_first` order
- **Stage order:** checks → changeset → publish → release

### Full Pipeline Pattern

```yaml
stages:
  checks: { needs: [] }
  changeset: { needs: [checks] }
  publish: { needs: [changeset] }
  release: { needs: [publish] }

concurrency: should_open_pr
concurrencies:
  - name: should_open_pr
    order: oldest_first

jobs:
  lint:
    stage: checks
    runs-on: library/node-22
    steps:
      - uses: actions/checkout
      - run: make lint

  changeset-check:
    stage: changeset
    if: "${{ cds.event_name == 'pull-request' }}"
    runs-on: library/node-22
    steps:
      - uses: actions/checkout
      - run: npx changeset status

  publish:
    stage: publish
    if: "${{ git.ref_name == 'master' }}"
    runs-on: library/node-22
    steps:
      - uses: actions/checkout
      - run: make publish

  release:
    stage: release
    needs: [publish]
    if: "${{ git.ref_name == 'master' }}"
    runs-on: library/default-container
    steps:
      - uses: actions/artifactoryRelease
        with:
          artifacts: "npm:*"
```

## Notifications

For VCS build status (`commit-status:`) and PR comment templates, see [Core Syntax > Workflow Structure](core-syntax.md#workflow-structure) and [Core Syntax > Triggers](core-syntax.md#triggers-on).

### Webex Notifications via c3pbot Gateway

There is **no** `library/c3pbot-send-message` action. Send Webex messages via `curl` to the c3pbot gateway.

**Requirements:**
- A CDS variable set (default: `c3pbot`) containing `gw_token_id` and `gw_token_secret`
- The Webex room ID to post to
- **EU region** is required for gateway access (`region: eu` on the job)

```yaml
# Template parameters: notification_room_id, c3pbot_variableset (default: "c3pbot")
# Variable set: vars: - [[.params.c3pbot_variableset]]

notify-webex:
  runs-on: ".cds/worker-models/node-22.yaml"
  region: eu
  needs: [main-job]
  if: ${{ needs.main-job.outputs.should-notify == 'true' && '[[.params.notification_room_id]]' != '' }}
  steps:
    - id: SendNotification
      run: |-
        #!/usr/bin/env bash
        set -Eeuo pipefail

        ROOM_ID="[[.params.notification_room_id]]"
        MESSAGE="${{ needs.main-job.outputs.notification-message }}"

        PAYLOAD=$(jq -n --arg roomId "${ROOM_ID}" --arg markdown "${MESSAGE}" \
          '{roomId: $roomId, markdown: $markdown}')

        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
          -X POST "https://<notification-gateway>/messages/${ROOM_ID}" \
          -H "Content-Type: application/json;charset=UTF-8" \
          -H "X-Ovh-Gateway-Source: ${{ vars.[[.params.c3pbot_variableset]].gw_token_id }}" \
          -H "X-Ovh-Gateway-Token: ${{ vars.[[.params.c3pbot_variableset]].gw_token_secret }}" \
          -H "X-Ovh-Gateway-Service-Name: c3pbot" \
          -d "${PAYLOAD}") || HTTP_CODE="000"

        if [ "${HTTP_CODE}" -ge 200 ] && [ "${HTTP_CODE}" -lt 300 ]; then
          printf "[INFO] Notification sent (HTTP %s)\n" "${HTTP_CODE}"
        else
          printf "[WARN] Notification failed (HTTP %s)\n" "${HTTP_CODE}"
        fi
```

Use `jq -n` for safe JSON construction. The `|| HTTP_CODE="000"` prevents `set -e` abort on network failures. Webex `markdown` field supports bold, lists, links, and `<@personEmail:…>` mentions.

## AsCode Permissions

Project permissions can be managed via YAML:

**Permission Roles:**
- Project: `read`, `manage`, `manage-worker-model`, `manage-action`, `manage-workflow`, `manage-workflow-template`
- Workflow: `trigger`
- VariableSet: `use`, `manage-items`

```yaml
# .cds/permissions.yaml
belongs_to:
  project_key: MY_PROJECT

permissions:
  - group: my-team
    role: manage
  - group: ci-users
    role: read

workflows:
  my-workflow:
    - group: deployers
      role: trigger

variablesets:
  my-secrets:
    - group: my-team
      role: manage-items
    - group: ci-users
      role: use
```
