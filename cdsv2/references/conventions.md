# CDSv2 Conventions & Style Guide

Code style, naming rules, boolean handling, and reference syntax — things to check when writing any CDS YAML.

## Contents
- [YAML Style](#yaml-style-cdsv2-files)
- [Workflow Shape](#workflow-shape)
- [Bash Script Conventions](#bash-script-conventions)
- [Naming Conventions (Complete)](#naming-conventions-complete)
- [Skip CI Markers](#skip-ci-markers)
- [Boolean Conditions Reference](#boolean-conditions-reference)
- [Cross-Repository References](#cross-repository-references)

## YAML Style (CDSv2 Files)

- **2-space indentation** (no tabs)
- **LF line endings**, UTF-8 encoding
- No trailing whitespace
- Final newline required
- Mark embedded shell scripts: `# yaml-embedded-languages: shell`
- **CRITICAL:** Preserve existing indentation when editing existing files

## Workflow Shape

- Do not add `stages:` or job `stage:` assignments for a workflow that has only
  one job. Stages are useful once the workflow has 2+ jobs to organize or order.

## Bash Script Conventions

Multi-line bash scripts in CDS steps must follow these conventions:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Logging format
printf "[INFO] %s\n" "message"
printf "[ERROR] %s\n" "message"

# Variable naming
EXPORTED_VAR="value"   # UPPERCASE for exports / environment
local_var="value"      # lowercase for local variables

# Always quote expansions
echo "${VAR}"          # CORRECT
echo $VAR              # WRONG — unquoted

# Export with worker
worker export my-key "my-value"
```

For a single command, prefer a one-line `run: <command>` without the preamble.

In a fresh disposable CDS job with no checkout or generated files to protect,
prefer running directly in the job workspace. Do not add `mktemp -d`, cleanup
traps, or `cd` indirection unless the step needs isolation from existing files
or runs multiple independent repositories side by side.

### `set -Eeuo pipefail` Explained

| Flag | Meaning |
|------|---------|
| `-E` | ERR traps are inherited by shell functions |
| `-e` | Exit immediately on error |
| `-u` | Treat unset variables as errors |
| `-o pipefail` | Pipeline fails if any command fails |

## Naming Conventions (Complete)

| Element | Convention | Examples |
|---------|------------|----------|
| Step IDs | PascalCase | `Requirements`, `Install`, `BuildArtifacts` |
| Action inputs | kebab-case | `auto-detect`, `node-version`, `registry-url` |
| Action file names | kebab-case | `setup-pnpm.yaml`, `cache-turbo.yaml` |
| Workflow file names | kebab-case | `build-deploy.yaml`, `release-pipeline.yaml` |
| Worker model file names | kebab-case | `node-22.yaml`, `default-vm.yaml` |
| Template file names | kebab-case | `my-template.yaml` |
| Template parameters | snake_case | `node_version_worker`, `deploy_region` |
| Gate inputs | kebab-case | `source-repository-branch`, `branch-to-clean`, `use-autodetect`, `target-languages` |
| Variable set keys | kebab-case | `api-key`, `staging-token` |
| Worker export keys | kebab-case | `should-install`, `build-result` |
| Job names | kebab-case | `lint-test`, `open-pull-request`, `build-deploy` |
| Environment variables | UPPER_SNAKE_CASE | `DOCKER_REGISTRY_URL`, `REGION`, `CDS_RUN_NUMBER` |

## Skip CI Markers

Include any of these in a commit message to skip workflow execution:
- `[skip ci]`
- `[ci skip]`
- `[no ci]`

```bash
git commit -m "docs: update README [skip ci]"
```

## Boolean Conditions Reference

Understanding when to compare booleans vs use them directly is critical:

### Gate Inputs (True Booleans)
Gate boolean inputs are actual booleans in CDS expressions. Use them **directly**:

```yaml
# CORRECT
if: ${{ gate.manual }}
if: ${{ gate.approve }}
if: ${{ gate.run-also-regular-push }}

# WRONG - don't compare to string
if: ${{ gate.run-also-regular-push == 'true' }}
```

### Step Outputs (String Values)
`worker export` always produces strings. Compare with string literals:

```yaml
# CORRECT
if: ${{ steps.Requirements.outputs.should-install == 'true' }}
if: ${{ steps.Requirements.outputs.should-install != 'true' }}

# A direct condition may work for string values such as "true", but explicit
# comparison is clearer and avoids surprises with other values.
if: ${{ steps.Requirements.outputs.should-install }}

# WRONG - the Not operator requires a real boolean, but step outputs are strings
if: ${{ !steps.Requirements.outputs.should-install }}
```

In bash, `worker export` outputs and action inputs are just strings after
interpolation or environment-variable assignment:

```bash
[ "${SHOULD_INSTALL}" = "true" ]
```

### Action Inputs (⚠️ YAML Boolean Trap)

CDS preserves YAML types in expressions. Boolean and string inputs behave differently:

| Input default | CDS `== 'true'` | CDS `== 'false'` | CDS truthiness | Bash value |
|---|---|---|---|---|
| `true` (boolean) | false | false | true | `"true"` |
| `"true"` (string) | **true** | false | true | `"true"` |
| `false` (boolean) | false | false | false | `"false"` |
| `"false"` (string) | false | **true** | false | `"false"` |

**Key observations:**

- **Boolean inputs are invisible to string comparisons.** CDS preserves YAML types -- a boolean `true` will never match `== 'true'` or `== 'false'`.
- **Truthiness works for both types.** Bare `${{ inputs.my-flag }}` correctly evaluates `true`/`"true"` as truthy and `false`/`"false"` as falsy.
- **The `!` operator is stricter than direct conditions.** It requires a real boolean. Avoid `!` on string-like action inputs and `worker export` outputs; use `!= 'true'` or another explicit comparison.
- **Bash erases type information.** Both types serialize to the same string in environment variables.

**Recommendations:**

- Quote boolean defaults in action inputs: `default: "false"` not `default: false`.
- Use string comparisons (`== 'true'`) when the input is a quoted string.
- Use truthiness checks (`${{ inputs.flag }}`) when type-safety across callers is needed.
- Use explicit negative string comparisons (`!= 'true'`) instead of `!` for step outputs and string-like inputs.
- Avoid `${VAR:+word}` for CDS boolean inputs in bash -- use `[ "${VAR}" = "true" ]` instead.

**Callers MUST always quote boolean-like values:**

```yaml
# CORRECT — string comparison will work in if: conditions
with:
  skip-processing: "true"
  generate-index: "false"

# WRONG — silently breaks if: conditions (boolean != string)
with:
  skip-processing: true
  generate-index: false
```

**Action defaults should also be quoted:**

```yaml
# CORRECT
inputs:
  skip-processing:
    default: "false"

# WRONG
inputs:
  skip-processing:
    default: false
```

**Bash boolean checks:**

```text
# In step condition (CDS expression)
if: ${{ inputs.auto-detect == 'true' }}

# In bash — use string comparison, not ${VAR:+word}
TAR_VERBOSE=""
[ "${VERBOSE}" = "true" ] && TAR_VERBOSE="-v"
tar -x ${TAR_VERBOSE} -f archive.tar.gz
```

## Cross-Repository References

```text
# Action from same project, different repo
- uses: shared-actions/my-action

# Action from different project
- uses: OTHERPROJECT/stash_ovh_net/team/shared-actions/my-action

# Remote action with branch/tag
- uses: dtcore/cicd-tools/setup-pnpm@master

# Template reference
from: DTCORE/stash_ovh_net/dtcore/cicd-tools/my-template@master
```

### Full Naming Syntax

Reference format for cross-project resources:
```
<PROJECT>/<VCS>/<REPO>/<ITEM>[@<BRANCH>]
```

Example: `DTCORE/stash_ovh_net/dtcore/cicd-tools/setup-pnpm@master`

### Skip Signature Verification

When referencing a repository that doesn't have GPG signing configured:

```yaml
repository:
  vcs: stash_ovh_net
  name: your_repository
  insecure_skip_signature_verify: true
```

For as-code permission management (`.cds/permissions.yaml`), see [Workflow Patterns > AsCode Permissions](workflow-patterns.md#ascode-permissions).
