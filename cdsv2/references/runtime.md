# CDSv2 Runtime & Infrastructure Reference

Runtime environment, infrastructure, and external services: worker model options, service containers, regions, integrations, caching, semver, staging deployment, and troubleshooting.

## Contents
- [Worker Model Options](#worker-model-options)
- [Service Container Patterns](#service-container-patterns)
- [Regions](#regions)
- [Integration Patterns](#integration-patterns)
- [Caching Patterns](#caching-patterns)
- [Semver Configuration](#semver-configuration)
- [Staging Deployment Pattern](#staging-deployment-pattern)
- [Troubleshooting & Tips](#troubleshooting--tips)

For worker model usage syntax (`runs-on:` patterns), see [Core Syntax > Worker Models](core-syntax.md#worker-models-runs-on). For custom worker model definitions (Docker/OpenStack YAML), see [Actions, Models & Templates > Worker Model Definitions](actions-models-templates.md#worker-model-definitions-cdsworker-modelsyaml).

## Worker Model Options

### Container Models

```yaml
# Basic container
runs-on: library/default-container

# With memory limit
runs-on:
  model: library/default-container
  memory: '8192'  # MB

# Language-specific containers
runs-on: library/go-1-26
runs-on: library/go-1-25
runs-on: library/npm-official-22-bookworm
runs-on: library/node-22
runs-on: library/python-3-12
```

### VM Models

```yaml
# Basic VM
runs-on: library/default-vm

# With flavor
runs-on:
  model: library/default-vm
  flavor: b2-7      # OVHcloud flavor

runs-on:
  model: library/Debian13-VM
  flavor: b2-15
```

### OpenStack Flavors

| Flavor | vCPU | RAM |
|--------|------|-----|
| XS | 2 | 4GB |
| S | 2 | 7GB |
| M | 4 | 15GB |
| L | 8 | 30GB |
| XL | 16 | 60GB |

```yaml
runs-on:
  model: library/default-vm
  flavor: M    # 4 vCPU, 15GB RAM
```

### VSphere Worker Models

- Only usable in `pcidss` region
- Cannot create custom models
- Supports `XS`, `S`, `M`, `L`, `XL` flavors; default is `S`

```yaml
jobs:
  build:
    region: pcidss
    runs-on:
      model: library/debian13-vsphere
      flavor: M
```

| Flavor | vCPU | RAM | Disk |
|--------|------|-----|------|
| XS | 4 | 8GB | 100GB |
| S | 6 | 8GB | 100GB |
| M | 12 | 16GB | 200GB |
| L | 24 | 32GB | 300GB |
| XL | 32 | 64GB | 400GB |

### Additional Worker Models

| Category | Models |
|----------|--------|
| Go | `library/go-1-22`, `library/go-1-23`, `library/go-1-24`, `library/go-1-25`, `library/go-1-26` |
| Python | `library/python-3-10`, `library/python-3-11`, `library/python-3-12`, `library/python-3-13`, `library/python-3-14` |
| Maven | `library/maven3-eclipse-temurin-8`, `-11`, `-17`, `-21` |
| Windows | `library/windows-chocolatey`, `library/windows-dotnet-fwk-4-8`, `library/windows-dotnet-sdk-6-0-1809`, `library/windows-dotnet-sdk-8-0-1809`, `library/windows-servercode-1809` |

## Service Container Patterns

### Database Testing

```yaml
jobs:
  test:
    runs-on: library/default-container
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        readiness:
          command: pg_isready -U test -d testdb
          interval: 5s
          timeout: 3s
          retries: 10
      redis:
        image: redis:7-alpine
        readiness:
          command: redis-cli ping
          interval: 2s
          timeout: 2s
          retries: 5
    steps:
      - run: |
          export DATABASE_URL="postgres://test:test@postgres:5432/testdb"
          export REDIS_URL="redis://redis:6379"
          ./run-tests.sh
```

### Message Queue Testing

```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management
    env:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    readiness:
      command: rabbitmq-diagnostics -q ping
      interval: 10s
      timeout: 5s
      retries: 5
```

## Regions

Jobs can target specific regions for network access and compliance:

| Region | Purpose | Worker Types |
|--------|---------|-------------|
| `default` | General builds, no internal access | Docker, OpenStack |
| `pcidss` | PCIDSS-compliant projects | Docker, VSphere |
| `us` | US deployment/service access | Docker only |
| `eu` | EU deployment/service access | Docker only |
| `labeu` | LABEU/DEVEU access | Docker only |
| `ca` | Canada access | Docker only |

```yaml
jobs:
  deploy-eu:
    region: eu
    runs-on: library/default-container
    steps:
      - run: ./deploy.sh

  deploy-pcidss:
    region: pcidss
    runs-on: library/vsphere-model
```

## Integration Patterns

For integration config access expressions (`integrations.artifact_manager.config.*`), see [Core Syntax > Integrations](core-syntax.md#integrations).

### Artifactory

#### Curl Pattern

```yaml
- run: |-
    #!/usr/bin/env bash
    set -Eeuo pipefail
    curl -sSL \
      -u "${{ integrations.artifact_manager.config.token_name }}:${{ integrations.artifact_manager.config.token }}" \
      "${{ integrations.artifact_manager.config.url }}github-release-remote/<org>/<repo>/..."
```

#### Full Pipeline

```yaml
name: full-pipeline
on: [push]

integrations: [artifactory-myproject]

jobs:
  build:
    runs-on: library/go-1-23
    steps:
      - uses: actions/checkout
      - run: make build
      - uses: actions/uploadArtifact
        with:
          path: bin/*

  package-docker:
    needs: [build]
    runs-on: library/default-vm
    steps:
      - uses: actions/checkout
      - uses: actions/downloadArtifact
        with:
          path: bin
      - run: docker build -t myapp:${{ cds.version }} .
      - uses: actions/dockerPush
        with:
          image: myapp
          tags: ${{ cds.version }}

  package-helm:
    needs: [build]
    runs-on: library/default-container
    steps:
      - uses: actions/checkout
      - uses: actions/helmPush
        with:
          chartFolder: ./charts/myapp

  release:
    needs: [package-docker, package-helm]
    if: "${{ git.ref_name == 'main' }}"
    runs-on: library/default-container
    steps:
      - uses: actions/artifactoryRelease
        with:
          artifacts: "docker:myapp:* helm:myapp"
```

### Arsenal Multi-Region Deployment

```yaml
name: multi-region-deploy
on: [push]

vars: [deployment-tokens]

gates:
  deploy-gate:
    if: "${{ git.ref_name == 'main' && gate.approve }}"
    inputs:
      approve:
        type: boolean

jobs:
  deploy:
    gate: deploy-gate
    strategy:
      matrix:
        region: [eu, us, ca]
    runs-on: library/default-container
    integrations:
      - arsenal-${{ matrix.region }}
    steps:
      - uses: actions/deployArsenal
        with:
          token: ${{ contextValue('vars', 'deployment-tokens', format('{0}-token', matrix.region)) }}
```

### Bitbucket

```yaml
# Access Bitbucket gateway tokens via variable sets
${{ vars.bitbucket.gw_token_id }}
${{ vars.bitbucket.gw_token_secret }}
```

## Caching Patterns

### Node.js (pnpm)

```yaml
- uses: actions/cache
  with:
    download-path: ${{ cds.workspace }}
    content: node_modules
    key: ${{ hashFiles('pnpm-lock.yaml') }}
```

### Turbo Monorepo Cache

```yaml
- uses: .cds/actions/cache-turbo.yaml
```

### Go Modules and Build Cache

Go has two caches with different invalidation: the **module cache** (`/go/pkg/mod`,
keyed on `go.mod` — module versions are immutable) and the **build cache** (`GOCACHE`,
keyed on `go.mod` + `go.sum`). Cache both with `actions/cache`.

**Key rule:** `download-path` is the **parent** of `content` — the cache extracts the
archive relative to `download-path`, so set it one level above the directory you cache.
Set `GOCACHE` explicitly at job level so Go writes to the cached path.

```yaml
jobs:
  build:
    runs-on: library/go-1-26
    env:
      GOCACHE: /root/.cache/go-build
    steps:
      - uses: actions/checkout
      - id: GoModCache
        uses: actions/cache
        with:
          download-path: /go/pkg            # parent of content
          content: /go/pkg/mod
          key: go-mod-${{ hashFiles('go.mod') }}
      - id: GoBuildCache
        uses: actions/cache
        with:
          download-path: /root/.cache       # parent of content
          content: /root/.cache/go-build
          key: go-build-${{ hashFiles('go.mod', 'go.sum') }}
      - run: go build ./...
```

Skip expensive steps on a hit with `if: ${{ steps.GoBuildCache.outputs.cache-hit == 'false' }}`.
Monorepo with multiple modules: widen the key, e.g. `hashFiles('go.mod', '**/go.mod', '**/go.sum')`.
For conditional download/save instead of the auto `Post-cache`, use `actions/cacheRestore` +
`actions/cacheSave` (those take `path:`, not `download-path`/`content`).

## Semver Configuration

For the basic npm and git semver syntax, see [Core Syntax > Semver Configuration](core-syntax.md#semver-configuration).

Additional semver sources:

```yaml
# From Helm chart
semver:
  from: helm
  path: charts/myapp/Chart.yaml
  release_refs: [refs/heads/main]

# From Yarn
semver:
  from: yarn
  path: package.json
  release_refs: [refs/heads/main]

# From Cargo.toml (Rust)
semver:
  from: cargo
  path: Cargo.toml
  release_refs: [refs/heads/main]

# From Debian control file
semver:
  from: debian
  path: debian/changelog
  release_refs: [refs/heads/main]

# From arbitrary file
semver:
  from: file
  path: VERSION
  release_refs: [refs/heads/main]

# From Python Poetry (pyproject.toml)
semver:
  from: poetry
  path: pyproject.toml
  release_refs: [refs/heads/main]
```

Tag Docker images and Helm charts with `${{ cds.version }}`.

## Staging Deployment Pattern

For staging environments:

- **Validate namespace:** Must be one of `dtcore`, `manager`, `ocms`, `order`
- **Validate region:** Must be one of `EU`, `CA`, `US`, `LABEU`
- **URL pattern:** `https://${branch}-${repo}.${region}.dtci.ovhcloud.tools`

## Troubleshooting & Tips

### Docker-in-Docker

Docker-in-Docker is **NOT possible** with Docker workers. Use OpenStack or vSphere worker models instead:

```yaml
runs-on:
  model: library/default-vm
  flavor: M
```

### Workflow Not Triggered

Common causes:
1. Check the **Explore** view in CDS UI for workflow status
2. Verify branch/path filters match your push
3. Check for `[skip ci]` in commit messages
4. Ensure workflow YAML is valid (use `cdsctl workflow lint`)

### Job Scheduling & Status

- **Statuses beyond Success/Fail:** a run can be `Crafting` (building the graph), `Blocked` (held by a concurrency rule), `Building`, `Cancelled`, `Stopped`, or `Skipped`. A job adds `Waiting` (queued for a worker), `Scheduling` (claimed by a hatchery), and `Retrying`. These surface in `cdsctl X workflow status` and `needs.<job>.result`.
- **Gates never time out.** An unapproved gate keeps the run `Building` indefinitely; the engine only re-evaluates it. There is no auto-cancel.
- **`retry:` is max 2** (3 executions total) with no delay between attempts. It is per-attempt and distinct from `cds.run_attempt`, which counts manual restarts.
- A job with no `steps:` and no `from:` completes as `Success` instantly without spawning a worker — useful as a DAG checkpoint.
- **All jobs skipped → the run ends `Skipped`, not `Success`.**

### Using CDSCTL in Jobs

`$CDS_API_URL` is pre-configured in all job workers:

```yaml
- run: |-
    #!/usr/bin/env bash
    set -Eeuo pipefail
    cdsctl workflow status "$CDS_PROJECT_KEY" "$CDS_WORKFLOW"
```

### VS Code Extension

A VS Code extension is available for CDS workflow editing with syntax highlighting and validation.
