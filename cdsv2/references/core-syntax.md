# CDSv2 Core Syntax Reference

Detailed syntax for CDSv2 workflows: structure, triggers, worker models, steps, built-in actions, contexts, expressions, variables, integrations, semver, concurrency, annotations, gates, matrix, services, external workflows, and a complete pipeline example.

## Contents

- [Directory Structure](#directory-structure)
- [Naming Conventions](#naming-conventions)
- [Workflow Structure](#workflow-structure)
- [Triggers](#triggers-on)
- [Worker Models](#worker-models-runs-on)
- [Steps](#steps)
- [Variable Export & Retrieval](#variable-export--retrieval)
- [Built-in Actions](#built-in-actions)
- [Expression Syntax](#expression-syntax-)
- [Variable Sets & Environment Variables](#variable-sets--environment-variables)
- [Integrations](#integrations)
- [Semver Configuration](#semver-configuration)
- [Concurrency Control](#concurrency-control)
- [Annotations](#annotations)
- [Job Dependencies & Stages](#job-dependencies--stages)
- [Job Outputs](#job-outputs)
- [Gates](#gates-manual-approval)
- [Matrix Strategy](#matrix-strategy)
- [Service Containers](#service-containers)
- [Workflow Templates](#workflow-templates)
- [External Workflow](#external-workflow-separate-repo)
- [Complete Example](#complete-example)

## Directory Structure

| Type | Path |
|------|------|
| Workflows | `.cds/workflows/<name>.yaml` |
| Actions | `.cds/actions/<name>.yaml` |
| Worker Models | `.cds/worker-models/<name>.yaml` |
| Templates | `.cds/workflow-templates/<name>.yaml` |

## Naming Conventions

| Element | Convention | Examples |
|---------|------------|----------|
| Step IDs | PascalCase | `Requirements`, `Install`, `BuildArtifacts` |
| Action inputs | kebab-case | `auto-detect`, `node-version`, `registry-url` |
| Template parameters | snake_case | `node_version_worker`, `deploy_region` |
| Job names | kebab-case | `lint-test`, `open-pull-request`, `build-deploy` |
| Environment variables | UPPER_SNAKE_CASE | `DOCKER_REGISTRY_URL`, `REGION`, `CDS_RUN_NUMBER` |

For the complete naming table (gate inputs, file names, variable set keys, worker export keys), see [Conventions > Naming](conventions.md#naming-conventions-complete).

**Action input ordering:** keep `inputs:` entries in alphabetical order. When adding a new input to an existing action, insert it at the correct alphabetical position rather than appending. Same rule for gate inputs and template parameters.

## Workflow Structure

```yaml
name: <string>
on: <string|list|map>       # Trigger events
vars: [<string>]            # Optional: variable sets
integrations: [<string>]    # Optional: Artifactory, Arsenal
commit-status:              # Optional: VCS build status
  title: "Build"
  description: "Running CI pipeline"
annotations:
  type: "ci"                # Custom annotations
jobs:
  <job_id>:
    name: <string>          # Optional: human-readable display name (useful in matrix)
    runs-on: <string|map>   # MANDATORY
    stage: <string>         # Optional: stage grouping
    needs: [<string>]       # Optional: job dependencies
    if: <expression>        # Optional: condition
    retry: 2                # Optional: max 2 retries
    region: eu              # Optional: eu, us, ca, labeu, pcidss, default
    continue-on-error: true # Optional: job-level (not just step)
    concurrency: my-rule    # Optional: job-level concurrency
    steps:
      - <step_definition>
```

**Skip CI:** Include `[skip ci]`, `[ci skip]`, or `[no ci]` in commit message to skip workflow execution.

**Retention:** Project-level only (deprecated in workflow YAML). Configure via as-code `project_retention`.

**Job Templates (`from:` at job level):**
```yaml
jobs:
  build:
    from: DTCORE/stash_ovh_net/dtcore/cicd-tools/my-job-template@master
    parameters:
      node_version: "22"
```

## Triggers (`on:`)

```text
# Simple
on: [push]

# Multiple events
on: [push, pull-request]

# With filters
on:
  push:
    branches:
      - main
      - 'release/**'
      - '!release/**-beta'       # Negation: exclude beta releases
    paths:
      - |
        src/**
        package.json
        !**/*.md                 # Negation: exclude docs
        !docs/**
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'  # Regex: semver tags only
  pull-request:
    types: [opened, reopened, closed, edited]   # CDS PR event types — no GitHub 'synchronize'
    branches: [main, develop]

# Scheduled (cron)
  schedule:
    - cron: '0 5 * * 1-5'  # Weekdays at 5 AM
    timezone: Europe/Paris

# Workflow chaining
  workflow-run:
    - workflow: PROJECT/vcs/repo/workflow-name
      status: [Success]
      branches: [main]            # Optional: filter by branch
      tags: ['v*']                # Optional: filter by tags
    # Event context: cds.event.workflow_run.{cds,git,username,conclusion,created_at,jobs.<id>.conclusion}
    # CAVEAT: the `status:` filter is currently not enforced by the engine — the
    # downstream workflow may trigger regardless of the upstream outcome, and
    # `branches:`/`tags:` filter the downstream definition's ref (not the upstream
    # run's). Gate inside the job on cds.event.workflow_run.conclusion instead.

# PR with comment template
  pull-request:
    paths: [".cds/workflows/*.yaml"]
    comment: |-
      [[- if ne .event.status "Success"]]
        :rotating_light: CDS report - check [here]([[ .cds.run_url ]])
        [[- if ne .jobs.checks.outputs.message "" ]]
        [[ .jobs.checks.outputs.message ]]
        [[- end ]]
      [[- end]]
    # Template context: .event.status, .cds.{workflow,run_number,run_attempt,run_url},
    # and .jobs.<id>.outputs.<key> for any output declared in the workflow's jobs.
    # The latter lets a failing job render its own diagnostic message inline in the
    # PR comment (see cicd-tools/changeset-ci-template for a real example). Comments
    # are sticky — CDS updates the same PR comment on each run.

```

**Map form needs explicit empty objects:** in the dictionary form of `on:`, an event with no filter must be written `push: {}` — a bare `push:` with no value is invalid. The string/array forms (`on: [push]`) don't need this.

**Path filter rule:** When using `paths`, put related include/exclude patterns in a single array entry, usually a block scalar as above. A single entry combines patterns together, so exclusions apply. Multiple entries are evaluated independently with OR logic, so a broad entry like `**/*` can make later exclusions ineffective.

**Default branch requirement:** `workflow-update`, `model-update`, `schedule`, and `workflow-run` triggers require the workflow or worker-model definition to exist on the repository default branch.

For webhook, PR comment, commit filter, and other advanced triggers, see [Workflow Patterns > Additional Triggers](workflow-patterns.md#additional-triggers).

## Worker Models (`runs-on:`)

```yaml
# Library models (most common)
runs-on: library/default-container  # Default Docker container
runs-on: library/default-vm         # OpenStack VM
runs-on: library/node-22            # Node.js specific
runs-on: library/go-1-26            # Go 1.26 container

# Local custom model
runs-on: .cds/worker-models/my-model.yaml

# Remote model
runs-on: PROJECT/vcs/repo/model-name

# With flavor/memory
runs-on:
  model: library/default-vm
  flavor: b2-7
  memory: "4096"
```

**Common Worker Models:**

| Category | Models |
|----------|--------|
| Default | `library/default-container`, `library/default-vm` |
| Node.js | `library/node-20`, `library/node-22`, `library/node-24`, `library/npm-official-22-bookworm` |
| Debian | `library/Debian12-VM`, `library/Debian13-VM`, `library/debian-bookworm`, `library/debian-bullseye`, `library/debian-trixie` |
| vSphere | `library/debian13-vsphere` |

For Go, Python, Maven, and Windows worker models, see [Runtime > Additional Worker Models](runtime.md#additional-worker-models).

For VM flavors, VSphere constraints, and memory options, see [Runtime > Worker Model Options](runtime.md#worker-model-options). For custom worker model definitions, see [Actions, Models & Templates > Worker Model Definitions](actions-models-templates.md#worker-model-definitions-cdsworker-modelsyaml).

## Steps

A step has either `run` OR `uses`, **never both**.

```yaml
steps:
  # Shell script (always use bash preamble)
  - id: Build
    run: |-
      #!/usr/bin/env bash
      set -Eeuo pipefail
      echo "Commands here"
      worker export result_value "output"

  # Using an action
  - uses: actions/checkout

  # Action with inputs
  - uses: actions/uploadArtifact
    with:
      path: "dist/**/*.tar.gz"
      if-no-files-found: error

  # Using local action
  - uses: .cds/actions/setup-pnpm.yaml

  # Using remote action
  - uses: dtcore/cicd-tools/setup-pnpm@master
    with:
      version: "10.20.0"

  # Conditional step
  - id: Deploy
    if: ${{ git.ref_name == 'main' }}
    run: make deploy

  # Continue on error
  - run: ./might-fail.sh
    continue-on-error: true

  # Step with environment variables
  - id: Test
    env:
      API_KEY: ${{ vars.myapp.api-key }}
    run: |-
      #!/usr/bin/env bash
      set -Eeuo pipefail
      make test
```

## Variable Export & Retrieval

```text
# Export in bash
worker export <key> <value>

# Retrieve in YAML
${{ steps.<step_id>.outputs.<key> }}      # Same job
${{ jobs.<job_id>.outputs.<key> }}        # Different job
```

`worker export` is the alias of the v2 `worker output` command. Pass the value as the second argument, or omit it to read from stdin (useful for multiline output):

```bash
printf '%s' "${REPORT}" | worker output report
```

## Built-in Actions

```yaml
# Checkout repository
- uses: actions/checkout
  with:
    ref: refs/heads/master    # Optional: specific ref
    path: subdirectory         # Optional: checkout path
    submodules: true           # Optional: true or 'recursive'
    depth: 1                   # Optional: shallow clone depth
    sha: abc123                # Optional: specific commit SHA
    git-url: ssh://git@<git-host>:7999/team/other-repo.git  # Optional: cross-repo checkout
# For external repositories, set sha: HEAD unless you intentionally checkout a known target-repo SHA.
# submodules accepts true or recursive; depth enables shallow clones.

# Upload artifact
- uses: actions/uploadArtifact
  with:
    path: "dist/**/*.tar.gz"  # MANDATORY
    if-no-files-found: error  # error|warn|ignore
    type: generic              # Optional: generic|coverage

# Download artifact
- uses: actions/downloadArtifact
  with:
    name: artifact-name       # Optional
    path: ./dest              # Optional
# Downloads only generic or coverage artifacts. If name is omitted, all matching artifacts are downloaded.

# Cache dependencies
- uses: actions/cache
  with:
    download-path: ${{ cds.workspace }}
    content: node_modules
    key: ${{ hashFiles('pnpm-lock.yaml') }}

# Cache notes:
# - content and key are REQUIRED; download-path (default ${{ cds.workspace }}) is the
#   PARENT directory the archive extracts into — set it one level above content
# - fail-on-cache-miss: true to fail step if cache not found
# - Storage: Artifactory when an integration exists, otherwise CDS CDN
# - Cache keys are case-sensitive
# - Auto "Post-cache" step runs at end of job to save cache

# Docker push (requires Artifactory integration, or explicit external registry auth)
- uses: actions/dockerPush
  with:
    image: my-group/my-image
    tags: ${{ cds.version }},latest  # Comma, space, or semicolon separated
    directory: .
    registry: external-registry.io     # Optional: external registry
    registryAuth: ${{ vars.docker.auth }} # Optional: base64 Docker-format auth
# Without Artifactory integration, registry and registryAuth are both required.

# Helm push (requires Artifactory integration)
- uses: actions/helmPush
  with:
    chartFolder: ./chart              # Default: ./chart
    chartVersion: ${{ cds.version }}  # Optional: override chart version
    appVersion: ${{ cds.version }}    # Optional
    skipUpdate: false                 # Optional
    updateDependencies: true          # Optional

# Arsenal deployment
- uses: actions/deployArsenal
  with:
    token: ${{ vars.myVarSet.token }}
    version: ${{ cds.version }}

# JUnit test results
- uses: actions/junit
  with:
    path: test-results.xml
    if-no-files-found: ignore
# This action fails when any test in the report failed; use continue-on-error if the workflow must continue.

# Artifactory release
- uses: actions/artifactoryRelease
  with:
    artifacts: "docker:**/* helm:*"

# Notes:
# - Can only be called ONCE per workflow run
# - 30-minute timeout
# - Creates a signed Release Bundle and retrieves SBOM from Xray
# - Conan artifacts NOT supported

# Add run result metadata
- uses: actions/addRunResult
  with:
    path: "package/-/package-1.0.0.tgz"
    type: npm   # Full list: conan, coverage, debian, deployment, docker,
                # generic, gradle, helm, maven, npm, puppet, python,
                # release, sbt, staticFiles, terraformProvider,
                # terraformModule, tests, nuget, variable
    payload: '{"key": "value"}'  # Optional: JSON metadata

# Promote artifacts between maturities (requires Artifactory integration)
- uses: actions/artifactoryPromote
  with:
    artifacts: "docker:myapp:* helm:myapp"  # Artifact filter
    maturity: "release"                      # Target maturity
    properties: "quality=stable"             # Optional properties
# 15-minute timeout; supports Docker, Helm, Debian, Conan, Generic, and Cargo artifacts.

# Restore-only cache (no auto-save)
- uses: actions/cacheRestore
  with:
    path: node_modules
    key: ${{ hashFiles('pnpm-lock.yaml') }}
    fail-on-cache-miss: false  # true to fail if not found
  # outputs: cache-hit (true/false)

# Save-only cache (no auto-restore)
- uses: actions/cacheSave
  with:
    path: node_modules
    key: ${{ hashFiles('pnpm-lock.yaml') }}

# Install SSH/PGP keys
- uses: actions/keyInstall
  with:
    keyName: my-deploy-key
    path: ~/.ssh/id_rsa       # Optional; default is ~/.ssh/id_rsa-${keyName}
```

For `debianPush`, `pythonPush`, and other extended built-in actions, see [Actions, Models & Templates > Built-in Actions (Extended)](actions-models-templates.md#built-in-actions-extended). For community-contributed actions (`library/*`), see [Actions, Models & Templates > Contrib Actions](actions-models-templates.md#contrib-actions-community-library).

## Expression Syntax (`${{ }}`)

### Contexts

| Context | Variables |
|---------|-----------|
| `cds` | `version`, `run_number`, `run_id`, `run_attempt`, `run_url`, `workflow`, `workspace`, `event_name`, `project_key`, `triggering_actor`, `version_next`, `workflow_ref`, `workflow_sha`, `workflow_vcs_server`, `workflow_repository`, `workflow_template`, `workflow_template_{ref,sha,vcs_server,repository,project_key,params}` (set when generated from a template), `job`, `stage`, `event`, `event.{schedule,payload,changesets,commit_message,workflow_run,workflow_run_id,cron,timezone,entity_updated,webhook_id}` |
| `git` | `ref`, `ref_name`, `ref_type`, `sha`, `sha_short`, `server`, `repository`, `repository_origin`, `repositoryUrl`, `repository_web_url`, `ref_web_url`, `commit_web_url`, `commit_message`, `author`, `author_email`, `semver_current`, `semver_next`, `changesets`, `pullrequest_id`, `pullrequest_to_ref_name`, `pullrequest_to_ref`, `pullrequest_web_url`, `connection`, `username`, `token`, `ssh_key`, `gpg_key`, `email` (last six are credentials/identity for git operations — keep them out of logs) |
| `vars` | `${{ vars.<set>.<key> }}` |
| `steps` | `${{ steps.<id>.outputs.<key> }}`, `.outcome`, `.conclusion` |
| `jobs` | `${{ jobs.<id>.outputs.<key> }}` |
| `needs` | `${{ needs.<job_id>.result }}`, `${{ needs.<job_id>.outputs.<key> }}` |
| `inputs` | `${{ inputs.<name> }}` — action inputs context |
| `gate` | `${{ gate.<input_name> }}` |
| `integrations` | `${{ integrations.<name>.config.<key> }}` — e.g. `.url`, `.token`, `.token_name`; `artifact_manager.config.build_info_prefix`, `.cds_repository`, `.platform`, `.project_key`, `.promotion_maturity_low/medium/high/release`, `.repository_prefix`, `.token`, `.token_name`, `.url`; `deployment.*` properties |
| `matrix` | `${{ matrix.<key> }}` |
| `env` | `${{ env.MY_VAR }}` |

### Bash Auto-Conversion

CDS contexts auto-convert to uppercase environment variables in bash:
- `cds.run_number` -> `$CDS_RUN_NUMBER`
- `git.ref_name` -> `$GIT_REF_NAME`

### Functions

```text
# Control flow
${{ success() }}    # All previous succeeded
${{ failure() }}    # Any previous failed
${{ always() }}     # Always run

# Job-level control flow
${{ cancelled() }}  # True if parent job was cancelled (job-level only)
${{ stopped() }}    # True if parent job was stopped (job-level only)

# Default/fallback
${{ coalesce(vars.myapp.url, env.DEFAULT_URL, 'http://localhost') }}  # First non-nil/non-empty
${{ default(vars.myapp.timeout, '30') }}  # Fallback if nil/empty

# String functions
${{ contains(git.ref_name, 'release') }}
${{ startsWith(git.ref_name, 'feature/') }}
${{ endsWith(git.ref_name, '-dev') }}
${{ format('build-{0}-{1}', git.sha_short, cds.run_number) }}
${{ toLower(cds.workflow) }}
${{ toUpper(git.ref_name) }}
${{ trimPrefix('v', git.semver_current) }}
${{ trimSuffix('.txt', 'file.txt') }}
${{ trimAll('/', '/path/') }}
${{ match(git.ref_name, 'release/*') }}
${{ join(fromJSON('["a","b"]'), ',') }}
${{ title('hello world') }}    # "Hello World" (capitalize first letter of each word)
${{ toTitle('hello world') }}  # "HELLO WORLD" (all uppercase — Go's ToTitle)

# JSON
${{ fromJSON(jobs.root.outputs.data) }}
${{ toJSON(matrix) }}
${{ toArray('single-value') }}

# Files
${{ hashFiles('package-lock.json', 'yarn.lock') }}

# Encoding
${{ b64enc(vars.myapp.secret) }}
${{ b64dec(env.ENCODED) }}
${{ b32enc('my-string') }}
${{ b32dec(env.ENCODED) }}

# Results (artifact metadata)
${{ result('generic', 'my-file.txt').md5 }}
${{ result('docker', 'my-image:latest').digest }}

# Dynamic context access
${{ contextValue('vars', 'myapp', format('{0}-token', matrix.region)) }}
```

### Engine Subtleties (Gotchas)

- **`contains(array, item)` and `match(str, pattern)` use glob, not equality/regex.** `contains([...], 'rel*')` matches by wildcard; `match` supports `**` and `!` negation: `match(git.ref_name, '**/* !master')`. String `contains`/`startsWith`/`endsWith` are case-insensitive.
- **`&&`, `||`, `!` require real booleans** — they do not return operand values GitHub-style. `${{ a && b }}` with string operands errors; use explicit comparisons.
- **No arithmetic** (`+ - * /`) in `${{ }}` — `*` is the array-projection token. (Templates `[[ ]]` do have `add`/`sub`/`mul`/`div`/`mod` — see actions-models-templates.md.)
- **`trimAll`/`trimPrefix`/`trimSuffix` take `(cutset, string)`** — cutset first: `trimPrefix('v', git.semver_current)`.
- **`.*` projects a field across an array** into a list: `git.changesets.*.path` → `join(...)` / `contains(...)`. Chaining `.*.*` is invalid.
- **Missing access differs by level:** a missing sub-key returns `""` (`git.nope == ''` is true), but an unknown *top-level* context (`foo.bar`) is a hard error.
- **`replace(input, old, new[, n])`** — optional 4th arg limits the number of replacements.

## Variable Sets & Environment Variables

```yaml
name: my-workflow
on: [push]

vars:
  - myApplication
  - sharedSecrets

env:
  GLOBAL_VAR: value

jobs:
  build:
    runs-on: library/default-container
    vars: [job-specific-vars]
    env:
      JOB_VAR: value
    steps:
      - run: echo "${{ vars.myApplication.api-key }}"
```

## Integrations

```yaml
# Artifactory — workflow level only, only ONE allowed
integrations: [artifactory-myproject-integration]

# Arsenal — can be at job level
jobs:
  deploy:
    integrations: [arsenal-eu]
    steps:
      - uses: actions/deployArsenal
        with:
          token: ${{ vars.myapp.arsenal-token }}
```

Access integration config:
- `${{ integrations.artifact_manager.config.url }}`
- `${{ integrations.artifact_manager.config.token }}`
- `${{ integrations.artifact_manager.config.token_name }}`

> **Opinionated Convention:** In our codebase, actions prefer accessing integration values via their **auto-converted environment variables** rather than CDS expressions. CDS auto-converts `integrations.artifact_manager.config.*` keys to uppercase env vars:
>
> | Expression | Env Var |
> |-----------|---------|
> | `integrations.artifact_manager.config.url` | `$CDS_INTEGRATION_ARTIFACT_MANAGER_URL` |
> | `integrations.artifact_manager.config.token` | `$CDS_INTEGRATION_ARTIFACT_MANAGER_TOKEN` |
> | `integrations.artifact_manager.config.token_name` | `$CDS_INTEGRATION_ARTIFACT_MANAGER_TOKEN_NAME` |
>
> This follows the same auto-conversion pattern as `cds.*` → `$CDS_*` and `git.*` → `$GIT_*`.

## Semver Configuration

```yaml
# From package.json (NPM)
semver:
  from: npm
  path: package.json
  release_refs: [refs/heads/master, refs/tags/v*]

# From git tags with custom schema
semver:
  from: git
  schema:
    "refs/heads/main": "${{ git.version }}-release-${{ cds.run_number }}"
    "refs/heads/develop": "${{ git.version }}-rc-${{ cds.run_number }}"
    "refs/heads/feature/*": "${{ git.version }}-dev-${{ git.sha_short }}"
    "**/*": "${{ git.version }}-snapshot-${{ cds.run_number }}"

```

For all semver sources (helm, yarn, cargo, debian, file, poetry), see [Runtime > Semver Configuration](runtime.md#semver-configuration).

Tag Docker images and Helm charts with `${{ cds.version }}`.

## Concurrency Control

A concurrency rule limits how many workflow runs or jobs execute in parallel. **Where you declare the rule defines its scope:**

| Declared at | Scope |
|---|---|
| Inside a workflow file (`concurrencies:` block) | That workflow and its jobs only |
| At project level (as-code or UI) | Shared across every workflow in the project |

To serialize across **different** workflows (or workflows generated from the same template), the rule must live at project level — declaring the same name inside two workflow files produces two independent queues.

### Settings

| Field | Default | Notes |
|---|---|---|
| `name` | — | CDS expressions allowed for dynamic naming (one queue per resolved value) |
| `description` | — | Optional, free-form |
| `pool` | `1` | Max parallel runs/jobs before queueing |
| `order` | `oldest_first` | Workflow: lowest `run_number` released first. Job: oldest queued first. `newest_first` is the reverse. |
| `cancel-in-progress` | `false` | If `true`, cancel the running run/job when a new one arrives |
| `if` | — | CDS expression; rule only applies when truthy |

### Examples

```yaml
# Workflow-scoped: declare and reference inline
name: my-workflow
concurrency: deploy
concurrencies:
  - name: deploy
    pool: 1
    order: oldest_first
```

```yaml
# Project-scoped: rule defined once at project level, just referenced here
name: my-workflow
concurrency: shared-deploy
```

For per-branch dynamic naming, job-level concurrency, the deadlock case, FIFO release timing, and template-specific guidance, see [Workflow Patterns > Concurrency Patterns](workflow-patterns.md#concurrency-patterns).

## Annotations

```yaml
name: my-workflow
on: [push]

annotations:
  commit: ${{ git.sha_short }}
  version: ${{ cds.version }}
  type: "🌿 ci"
```

> **Opinionated Convention:** Our codebase uses emoji-prefixed annotation types. This is NOT a CDS requirement — it's our team convention for visual categorization in the CDS UI.

| Emoji | Type | Usage |
|-------|------|-------|
| 🌿 | `ci` | Standard CI workflows |
| 🧪 | `test` | Test-focused workflows |
| 🧰 | `utilities` | Utility/tooling workflows |
| 🚀 | `arsenal-labeu` | Arsenal deployment workflows |
| 🛠️ | `worker-model` | Worker model CI workflows |
| 🧹 | `clean` | Cleanup/staging teardown workflows |

**Retention:** Project-level only (deprecated in workflow YAML). See project as-code configuration.

## Job Dependencies & Stages

Use `stages.<stage>.needs` for ordering between stages. Use `jobs.<job>.needs`
only for dependencies between jobs in the same stage; cross-stage job `needs`
is invalid.

```yaml
# Direct dependencies
jobs:
  build:
    runs-on: library/default-container
    steps:
      - run: make build
  test:
    needs: [build]
    runs-on: library/default-container
    steps:
      - run: make test
  deploy:
    needs: [build, test]
    if: "${{ git.ref_name == 'main' && success() }}"
    runs-on: library/default-container
    steps:
      - run: make deploy

# Stage-based organization
stages:
  checks: { needs: [] }
  build: { needs: [] }
  release: { needs: [publish] }

jobs:
  lint:
    stage: checks
    runs-on: library/default-container
    steps:
      - run: make lint
```

## Job Outputs

```yaml
jobs:
  build:
    runs-on: library/default-container
    steps:
      - id: GetVersion
        run: worker export version "1.2.3"
    outputs:
      version:
        value: ${{ steps.GetVersion.outputs.version }}

  deploy:
    needs: [build]
    runs-on: library/default-container
    steps:
      - run: echo "Deploying ${{ jobs.build.outputs.version }}"
```

## Gates (Manual Approval)

```yaml
gates:
  prod-deploy:
    if: "${{ success() && (git.ref_name == 'main' || gate.manual) }}"
    inputs:
      approve:
        type: boolean
    reviewers:
      groups: [release-team]
      users: [john.doe]

jobs:
  deploy:
    gate: prod-deploy
    needs: [build]
    runs-on: library/default-container
    steps:
      - run: ./deploy.sh
```

**Input types:** the only real `type:` values are `boolean` and `number`; anything else (including `text`) is treated as a string. A "choice" input is not a type — it is the `options:` block (`values:` + `multiple:`) on any input, and CDS validates the submitted value against `values`.

For detailed boolean rules (gate vs step vs action input), see [Conventions > Boolean Conditions Reference](conventions.md#boolean-conditions-reference).

For choice inputs, text inputs, and conditional gate patterns, see [Workflow Patterns > Gate Patterns](workflow-patterns.md#gate-patterns).

## Matrix Strategy

```yaml
jobs:
  test:
    runs-on: library/default-container
    strategy:
      matrix:
        os: [ubuntu, debian]
        arch: [amd64, arm64]
        version: ['1.21', '1.22']
    steps:
      - run: echo "Testing ${{ matrix.os }}-${{ matrix.arch }} v${{ matrix.version }}"

  # Dynamic matrix from previous job
  deploy:
    needs: [setup]
    strategy:
      matrix:
        service: ${{ fromJSON(jobs.setup.outputs.services) }}
    runs-on: library/default-container
    steps:
      - run: ./deploy.sh ${{ matrix.service }}
```

For dynamic matrices from job outputs and named matrix jobs, see [Workflow Patterns > Matrix Patterns](workflow-patterns.md#matrix-patterns).

## Service Containers

```yaml
jobs:
  test:
    runs-on: library/default-container
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        readiness:
          command: pg_isready -U postgres
          interval: 10s
          timeout: 5s
          retries: 5
      redis:
        image: redis:7
    steps:
      - run: ./run-tests.sh
```

For database, Redis, and message queue patterns, see [Runtime > Service Container Patterns](runtime.md#service-container-patterns).

## Workflow Templates

Templates use Go template syntax with `[[` `]]` delimiters (not `{{ }}`). Parameters use snake_case. Key syntax: `[[.params.param_name]]` for values, `[[- if .params.flag ]]` / `[[- end ]]` for conditionals, `[[ .cds.workflow ]]` for CDS context.

For template authoring, helper functions, and consumer-side usage, see [Actions, Models & Templates > Workflow Templates](actions-models-templates.md#workflow-templates-cdsworkflow-templatesyaml).

## External Workflow (Separate Repo)

```yaml
name: external-code-workflow
repository:
  vcs: stash_ovh_net
  name: team/my-source-code-repo
on: [push, workflow-update]

jobs:
  build:
    runs-on: library/default-container
    steps:
      - uses: actions/checkout
      - run: make build
```

## Complete Example

```yaml
name: complete-pipeline
on:
  push:
    branches: [master, develop]
  pull-request:
    types: [opened, reopened]
    comment: |-
      [[- if ne .event.status "Success"]]
        #### :rotating_light: CDS report ([[ .cds.workflow ]]#[[ .cds.run_number ]].[[ .cds.run_attempt ]])
        Check it [here]([[ .cds.run_url ]]).
      [[- end]]

vars: [myapp]
integrations: [artifactory-myproject]

semver:
  from: npm
  path: package.json
  release_refs: [refs/heads/master]

annotations:
  type: ci
  commit: ${{ git.sha_short }}

stages:
  checks: { needs: [] }
  publish: { needs: [checks] }
  release: { needs: [publish] }

jobs:
  lint-test:
    stage: checks
    runs-on: .cds/worker-models/node-22.yaml
    region: eu
    steps:
      - uses: actions/checkout
      - uses: .cds/actions/setup-pnpm.yaml
      - id: CacheNodeModules
        uses: actions/cache
        with:
          download-path: ${{ cds.workspace }}
          content: node_modules
          key: ${{ hashFiles('pnpm-lock.yaml') }}
      - id: Install
        run: |-
          #!/usr/bin/env bash
          set -Eeuo pipefail
          if [ -f Makefile ]; then make install; else pnpm install; fi
      - id: Lint
        run: |-
          #!/usr/bin/env bash
          set -Eeuo pipefail
          if [ -f Makefile ]; then make lint; else pnpm run lint; fi
      - id: Test
        run: |-
          #!/usr/bin/env bash
          set -Eeuo pipefail
          if [ -f Makefile ]; then make test; else pnpm test; fi

  publish:
    stage: publish
    if: "${{ git.ref_name == 'master' && success() }}"
    runs-on: .cds/worker-models/node-22.yaml
    steps:
      - uses: actions/checkout
      - uses: .cds/actions/setup-pnpm.yaml
      - id: CacheNodeModules
        uses: actions/cache
        with:
          download-path: ${{ cds.workspace }}
          content: node_modules
          key: ${{ hashFiles('pnpm-lock.yaml') }}
      - id: Install
        run: |-
          #!/usr/bin/env bash
          set -Eeuo pipefail
          if [ -f Makefile ]; then make install; else pnpm install; fi
      - id: Publish
        run: |-
          #!/usr/bin/env bash
          set -Eeuo pipefail
          PACKAGE_VERSION="$(node -e "console.log(require('./package.json').version);")"
          worker export package_version "${PACKAGE_VERSION}"
          if [ -f Makefile ]; then make publish; else pnpm publish; fi
      - id: AddRunResult
        uses: actions/addRunResult
        with:
          path: "myapp/-/myapp-${{ steps.Publish.outputs.package_version }}.tgz"
          type: npm
    outputs:
      version:
        value: ${{ steps.Publish.outputs.package_version }}

  release:
    stage: release
    runs-on: library/default-container
    steps:
      - uses: actions/artifactoryRelease
        with:
          artifacts: "npm:*"
```
