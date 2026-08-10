#!/usr/bin/env bash
# install.sh — Install all skills listed in registry.json via 'npx skills add'.
#
# Usage:
#   ./install.sh                  # install everything (skip TBD entries by default)
#   ./install.sh --all            # also attempt TBD entries (will warn/error)
#   ./install.sh --dry-run        # show what would run, don't execute
#   ./install.sh --only <name>    # install a single skill by name
#   ./install.sh --global         # install globally (skip if agent doesn't support it)
#
# Replaces the old model of versioning SKILL.md content with declarative
# installation from skills.sh manifests.

set -uo pipefail

REGISTRY="${REGISTRY:-$(dirname "$0")/registry.json}"

DRY_RUN=false
ALL=false
ONLY=""
GLOBAL=false
YES=true

for arg in "$@"; do
  case "$arg" in
    --dry-run)    DRY_RUN=true; YES=false ;;
    --all)        ALL=true ;;
    --only=*)     ONLY="${arg#--only=}" ;;
    --only)       shift; ONLY="${1:-}" ;;
    --global|-g)  GLOBAL=true ;;
    --project|-p) GLOBAL=false ;;
    --no-yes)     YES=false ;;
    -h|--help)
      sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [[ ! -f "$REGISTRY" ]]; then
  echo "ERROR: registry not found at $REGISTRY" >&2
  exit 1
fi

echo "→ Registry: $REGISTRY"
echo

# Pilot the whole loop from Python to avoid bash read/process-substitution bugs.
PYTHON_RUNNER="$(cat <<PYEOF
import json, subprocess, sys

REGISTRY = "$REGISTRY"
ONLY = "$ONLY"
ALL = "$(echo $ALL)" == "true"
DRY_RUN = "$(echo $DRY_RUN)" == "true"
YES = "$(echo $YES)" == "true"
GLOBAL = "$(echo $GLOBAL)" == "true"

with open(REGISTRY) as f:
    reg = json.load(f)

skills = reg["skills"]
print(f"→ Found {len(skills)} skills")
print()

installed = 0
skipped = 0
failed = 0

for s in skills:
    name = s["name"]
    owner = s["owner"]
    repo = s["repo"]
    source = s.get("source", "")

    if ONLY and name != ONLY:
        continue

    if owner == "TBD":
        if ALL:
            print(f"⚠ {name} — TBD upstream, attempting anyway")
        else:
            print(f"⊘ {name} — TBD upstream, skipped (use --all to attempt)")
            skipped += 1
            continue

    flags = []
    if YES:
        flags.append("-y")
    if GLOBAL:
        flags.append("-g")

    cmd = ["npx", "skills", "add", f"https://github.com/{owner}/{repo}", "--skill", name] + flags
    print(f"+ {' '.join(cmd)}")

    if DRY_RUN:
        print("  (dry-run: skipped)")
        continue

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("  ✓ installed")
            installed += 1
        else:
            err = result.stderr.strip().splitlines()
            tail = err[-1] if err else "unknown error"
            print(f"  ✗ failed: {tail}")
            failed += 1
    except subprocess.TimeoutExpired:
        print("  ✗ timeout")
        failed += 1
    except Exception as e:
        print(f"  ✗ exception: {e}")
        failed += 1

print()
print(f"Done. installed={installed} skipped={skipped} failed={failed}")
sys.exit(0 if failed == 0 else 1)
PYEOF
)"

python3 -c "$PYTHON_RUNNER"
