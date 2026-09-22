# CDSv2 Actions & Templates Authoring

Authoring guide for custom actions, worker models, workflow templates, and community contrib actions.

## Contents
- [Custom Actions](#custom-actions-cdsactionsyaml)
- [Contrib Actions (Community Library)](#contrib-actions-community-library)
- [Built-in Actions (Extended)](#built-in-actions-extended)
- [Worker Model Definitions](#worker-model-definitions-cdsworker-modelsyaml)
- [Workflow Templates](#workflow-templates-cdsworkflow-templatesyaml)

## Custom Actions (`.cds/actions/*.yaml`)

### Action Structure

```yaml
name: "My Action"
description: "Description (upstream-reference)"

inputs:
  auto-detect:        # kebab-case for inputs
    description: "Auto-detect version"
    default: true
  node-version:
    description: "Node.js version"
    default: "22.19.0"

outputs:
  result:
    value: ${{ steps.Install.outputs.result }}

runs:
  steps:
    - id: Requirements
      run: |-
        #!/usr/bin/env bash
        set -Eeuo pipefail
        # Check if tool is already installed
        if command -v mytool &>/dev/null; then
          worker export should-install false
        else
          worker export should-install true
        fi

    - id: Install
      if: ${{ steps.Requirements.outputs.should-install == 'true' }}
      run: |-
        #!/usr/bin/env bash
        set -Eeuo pipefail
        # Install tool, export outputs
        VERSION=$(trimPrefix 'v' '${{ inputs.node-version }}')
        # ... installation logic
        worker export result "installed-${VERSION}"
```

### Output Types

```yaml
outputs:
  result:
    value: ${{ steps.Install.outputs.result }}
  binary-path:
    value: "${{ steps.Build.outputs.path }}"
    type: path  # Adds the value to PATH environment variable
```

### Post-Execution Hook

Actions can define a `post` step that runs at the end of the job, regardless of step success:

```yaml
runs:
  post: echo 'Cleanup done'  # Executed at end of job
  steps:
    - id: Install
      run: |-
        #!/usr/bin/env bash
        set -Eeuo pipefail
        # Main steps...
```

### Key Action Patterns

1. **Requirements Step First:** Always start with a `Requirements` step that checks if the tool/dependency is already installed
2. **Conditional Installation:** Use `worker export should-install true/false` for conditional execution of subsequent steps
3. **Idempotency:** Check if tool exists before installing (`command -v`, `which`, file existence)
4. **Version Normalization:** Use `trimPrefix('v', inputs.version)` to remove `v` prefix from versions
5. **Naming:** Follow [Conventions > Naming](conventions.md#naming-conventions-complete) (inputs: kebab-case, step IDs: PascalCase)
6. **Input Ordering:** Keep `inputs:` entries alphabetical. When adding a new input, insert it at the correct alphabetical position — do not append at the end. Same rule for gate inputs and template parameters.

**No `required` on action inputs:** custom action `inputs` only have `description` and `default` — there is no `required:` field (it is silently ignored if written). Enforce mandatory inputs by validating in a `Requirements` step. (Template parameters, by contrast, do support `required:`.)

### Action with `runs-on` (Standalone)

```yaml
name: my-standalone-action
description: Runs in its own worker
inputs:
  message:
    description: Message to print
    default: "Hello"
runs:
  runs-on: library/default-container
  steps:
    - run: echo "${{ inputs.message }}"
```

### Action without `runs-on` (Composable)

When `runs-on` is omitted, the action runs inside the calling job's worker:

```yaml
name: setup-pnpm
description: Install pnpm package manager
inputs:
  version:
    description: pnpm version
    default: "10.20.0"
runs:
  steps:
    - id: Install
      run: |-
        #!/usr/bin/env bash
        set -Eeuo pipefail
        npm install -g pnpm@${{ inputs.version }}
```

For action usage syntax (`uses:` with local/remote paths), see [Core Syntax > Steps](core-syntax.md#steps).

## Contrib Actions (Community Library)

Contrib actions live in `CDSPUBLIC/stash_ovh_net/cds/cds-ovh-contrib/` and are referenced as `library/<action-name>`.

| Action | Description |
|--------|-------------|
| `library/artifactory-docker-login` | `docker login` to an Artifactory registry using the workflow's Artifactory integration creds (input: `registry`) |
| `library/artifactory-download-latest-cds-artifact` | Download the latest CDS artifact version from Artifactory |
| `library/artifactory-meta-release-create` | Create Artifactory release metadata |
| `library/artifactory-pull-latest-docker-image` | Pull the latest Docker image version from Artifactory |
| `library/artifactory-reindex` | Trigger a package-index rebuild on the tenant's Artifactory repos (recovery / manual-upload — not needed in normal publish flows) |
| `library/bitbucket-comment-pr` | Comment on a Bitbucket PR (needs `region: eu`) |
| `library/bitbucket-create-pr` | Create Bitbucket pull request (needs `region: eu`) |
| `library/bitbucket-get-pr` | Get PR details from Bitbucket |
| `library/bitbucket-wait-pr` | Poll-wait for a Bitbucket PR to merge (`interval`/`timeout` in min; needs `region: eu`) |
| `library/cds-trigger-workflow` | Trigger another CDS workflow |
| `library/curl-upload-artifact` | Upload artifact via curl |
| `library/deploy-arsenal-alternative` | Alternative Arsenal deployment |
| `library/docker-scout-compare` | Docker Scout image comparison |
| `library/docker-scout-quickview` | Docker Scout quick view |
| `library/gh-create-pr` | Create GitHub pull request |
| `library/gh-get-pr` | Get GitHub PR details |
| `library/installHelm` | Install Helm CLI |
| `library/installKubectl` | Install kubectl CLI |
| `library/kaniko-build-push` | Build and push Docker image with Kaniko |
| `library/nuget-upload` | Upload NuGet packages |
| `library/playwright-install` | Install Playwright browsers |
| `library/python-package` | Build Python package |
| `library/python-upload` | Upload Python package to registry |
| `library/semantic-release` | Automated semantic versioning |
| `library/sonarcloud-analysis` | SonarCloud code analysis |
| `library/sonarqube-analysis` | SonarQube code analysis |
| `library/servicenow-change-create` | Create a ServiceNow change |
| `library/servicenow-change-close` | Close a ServiceNow change |
| `library/setup-go` | Install Go and expose `install-path` and `gobin` outputs; default Go version is `1.26.0` |
| `library/terraform-apply` | Terraform apply |
| `library/terraform-plan` | Terraform plan |
| `library/trivy-scan` | Trivy security scan |

**Usage:**
```text
- uses: library/bitbucket-create-pr
  with:
    title: "My PR"
# outputs: pr-id, pr-link

# Some contrib actions require specific regions:
jobs:
  create-pr:
    region: eu  # Required for bitbucket-create-pr
    runs-on: library/default-container
    steps:
      - uses: library/bitbucket-create-pr
```

## Contrib Workflow Templates (Community Library)

Shared workflow templates published as `library/<name>` and consumed via `from: library/<name>` (optionally pinned `@vX.Y.Z`). Like contrib actions, they live in the CDS public space; pass parameters from the consumer workflow.

| Template | Description |
|----------|-------------|
| `library/ai-review` | AI-powered PR code review (codeur + OVHcloud AI Endpoints) posting inline Bitbucket comments. Advisory (`continue-on-error`, never blocks the PR); runs as the triggering user's AI identity. Only `artifactory_integration` is required. |
| `library/renovate` | Runs Renovate to open dependency-update PRs (Bitbucket Server / Forgejo); private-registry auth wired from the Artifactory integration. |
| `library/arsenal-deploy` | Deploy an application to one Arsenal region (region passed as a parameter). |
| `library/arsenal-deploy-docker` | Language-agnostic full lifecycle: Docker build & push, Helm chart gen & push, staging → release promote → production deploy on Arsenal. |
| `library/arsenal-regions-list` | Derive region lists dynamically from a variable set (`<region>-token` pattern); exports `staging-regions` / prod regions for a downstream matrix. |
| `library/core-platform-uservice-api` | Golang archetype: build, test, and deploy a Go service across all Arsenal regions. |
| `library/terraform-module-publish` | Publish Terraform modules. |
| `library/terraform-provider-build-and-publish` | Build and publish Terraform providers. |

**Usage (consumer workflow):**
```yaml
# .cds/workflows/ai-review.yml
name: ai-review
on:
  pull-request:
    types: [opened, reopened, edited]
from: library/ai-review
parameters:
  artifactory_integration: artifactory-<namespace>-<component>
```

## Built-in Actions (Extended)

These built-in actions are less commonly used. For the core built-in actions, see [Core Syntax > Built-in Actions](core-syntax.md#built-in-actions).

### debianPush

Push Debian packages to Artifactory (requires Artifactory integration):

```yaml
- uses: actions/debianPush
  with:
    files: "*.deb"
    architectures: amd64
    components: main
    distributions: stable
    label: my-package
    origin: my-team
```

### pythonPush

**DEPRECATED:** Use contrib actions `library/python-package` + `library/python-upload` instead.

## Worker Model Definitions (`.cds/worker-models/*.yaml`)

```yaml
name: node-22
type: docker
osarch: linux/amd64
spec:
  image: registry.example.com/cds-nodejs-worker:22-bookworm
```

### Worker Model Requirements

- **Default RAM:** 6048 MB
- **Required tool:** `curl` is the ONLY technical requirement in worker images
- **Image source:** Must come from Artifactory Docker registry
- **Access:** `cds_workers` group needs read access to the Docker repository in Artifactory

### Worker Model Spec Fields

Beyond `image`, the spec accepts:

- **docker:** `username`, `password`, `envs` (a map injected into every worker spawned from the model — handy for proxy / registry config set once).
- **openstack:** `flavor`.
- **vsphere:** `flavor`, `username`, `password`.
- Top-level: `description`.

```yaml
# Minimal custom worker model
name: my-model
type: docker
osarch: linux/amd64
spec:
  image: artifactory.example.com/docker-repo/my-image:latest
  # Image MUST have curl installed
  # cds_workers group MUST have read access to docker-repo
```

### OpenStack VM Model

```yaml
name: my-vm-model
description: Custom Debian VM
type: openstack
osarch: linux/amd64
spec:
  image: cds_import_my-custom-image
```

For worker model usage syntax (`runs-on:` patterns and available models), see [Core Syntax > Worker Models](core-syntax.md#worker-models-runs-on).

## Workflow Templates (`.cds/workflow-templates/*.yaml`)

Templates use **Go template syntax** with `[[` `]]` delimiters (not `{{` `}}`).

### Template Definition

```yaml
name: my-template

parameters:
  - key: node_version_worker    # snake_case for parameters
    default: ".cds/worker-models/node-22.yaml"
  - key: enable_tests
    required: false
    default: "true"
  - key: team_name
    required: true
  - key: source_repository_git_url
    required: true

spec: |-
  name: [[.cds.workflow]]
  on: [push]

  vars:
    - [[ .params.team_name ]]

  jobs:
    build:
      runs-on: [[.params.node_version_worker]]
      steps:
        - uses: actions/checkout
        [[- if .params.enable_tests ]]
        - run: make test
        [[- end ]]
        - run: make build
```

### Parameter Types

Parameters are strings by default. Set `type: json` to have the value (and its `default`) parsed as JSON before rendering — this enables `[[ range ]]` over arrays/maps:

```yaml
parameters:
  - key: regions
    type: json
    default: '["eu","us"]'
spec: |-
  jobs:
    deploy:
      strategy:
        matrix:
          region:
          [[- range .params.regions ]]
            - [[ . ]]
          [[- end ]]
```

Parameters also support `required: true` (unlike action inputs).

### Template Interpolation Syntax

| Syntax | Purpose | Example |
|--------|---------|---------|
| `[[.params.param_name]]` | Parameter value | `[[.params.node_version_worker]]` |
| `[[- if .params.param_name ]]` | Conditional block | `[[- if .params.enable_tests ]]` |
| `[[- end ]]` | End conditional | — |
| `[[ .cds.workflow ]]` | CDS context | Workflow name |
| `[[ .cds.run_number ]]` | CDS context | Run number |

**Note:** The `-` in `[[- if` trims whitespace before the tag. Use it to avoid blank lines in output.

### Template Escaping (Go Template Delimiters)

When a template's `spec:` block contains bash `[[ ]]` conditionals (e.g., `[[ -n "$VAR" ]]`), they conflict with Go template `[[ ]]` delimiters. Escape them using the `[["[["]]` and `[["]]"]]` pattern:

```yaml
# In a workflow template spec:
spec: |-
  jobs:
    deploy:
      steps:
        - run: |-
            #!/usr/bin/env bash
            set -Eeuo pipefail
            # Escaped bash conditionals inside Go template
            if [["[["]] -n "${BRANCH}" [["]]"]]; then
              echo "Branch is set"
            fi
```

This is used in `changeset-ci-template` and `clean-staging-template` where bash conditionals coexist with Go template interpolation.

### Template Helper Functions

Templates support Sprig-based helper functions in `[[` `]]` delimiters:

**String Functions:**
- `abbrev`, `trunc`, `trim`, `upper`, `lower`, `title`, `untitle`
- `substr`, `repeat`, `nospace`, `initials`, `swapcase`, `shuffle`
- `snakecase`, `camelcase`

**Random:**
- `randAlphaNum`, `randAlpha`, `randASCII`, `randNumeric`

**Quoting & Formatting:**
- `quote`, `squote` — add double/single quotes
- `indent`, `nindent` — indent text (nindent adds newline first)

**Replacement:**
- `replace` — string replacement
- `plural` — pluralize words

**Type Conversion:**
- `toString`, `default`, `empty`, `coalesce`

**Math & Misc:**
- `add`, `sub`, `mul`, `div`, `mod` — integer arithmetic (not available in `${{ }}`)
- `ternary` — `[[ ternary "yes" "no" .params.flag ]]`
- `urlencode`, `dirname`, `basename`

**JSON/Encoding:**
- `toJSON`, `toPrettyJSON` — serialize to JSON
- `b64enc`, `b64dec` — Base64 encode/decode
- `escape` — escape special characters

**Example usage in templates:**
```yaml
spec: |-
  name: [[.cds.workflow]]
  jobs:
    build:
      env:
        APP_NAME: [[ .params.app_name | upper | trunc 63 ]]
        ENCODED: [[ .params.secret | b64enc ]]
        SLUG: [[ .params.branch | snakecase ]]
        CONFIG: [[ .params.config | toJSON ]]
```

### Template Merge Semantics

- A template's `on:` is applied only if the consumer workflow defines no `on:`; otherwise it is ignored — a template cannot force triggers.
- Template `annotations:` merge into the workflow, but consumer keys win on collision.
- Workflow-level `concurrency:` in a template `spec` is ignored (see [Workflow Patterns > Concurrency Patterns](workflow-patterns.md#concurrency-patterns)); only job-level concurrency takes effect.

### Using Templates (Consumer Side)

```yaml
# .cds/workflows/my-workflow.yaml
name: my-workflow
from: DTCORE/stash_ovh_net/dtcore/cicd-tools/my-template@master

parameters:
  team_name: "my-team"
  source_repository_git_url: "ssh://git@<git-host>:7999/team/my-repo.git"
  enable_tests: "true"
```

For boolean handling rules (gate booleans vs string outputs), see [Conventions > Boolean Conditions Reference](conventions.md#boolean-conditions-reference).
