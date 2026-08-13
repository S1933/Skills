#!/usr/bin/env bash
# install.sh — Wipe locally installed skills (gitignore-respecting), regenerate
# skills-lock.json, then install every skill declared in registry.json via
# 'npx skills add'.
#
# Usage:
#   ./install.sh            # wipe + install everything
#   ./install.sh --dry-run  # show what would happen, do nothing
#
# Replaces the old model of versioning SKILL.md content with declarative
# installation from skills.sh manifests.

set -uo pipefail

REGISTRY="${REGISTRY:-$(dirname "$0")/registry.json}"
GITIGNORE="$(dirname "$0")/.gitignore"
INSTALL_ROOT="$HOME/.agents/skills/.agents/skills"
LOCKFILE="$(dirname "$0")/skills-lock.json"

DRY_RUN=false
case "${1:-}" in
  --dry-run)  DRY_RUN=true ;;
  -h|--help)
    sed -n '2,9p' "$0"; exit 0 ;;
  "")         ;;
  *)
    echo "ERROR: unknown arg: $1" >&2
    echo "Usage: $0 [--dry-run]" >&2
    exit 2
    ;;
esac

# ---- Wipe installed skills (gitignore-respecting)
if [[ -d "$INSTALL_ROOT" ]]; then
  declare -a KEEP_PATTERNS=()
  if [[ -f "$GITIGNORE" ]]; then
    while IFS= read -r raw; do
      line="${raw%%#*}"
      line="$(echo "$line" | xargs || true)"
      [[ -z "$line" ]] && continue
      KEEP_PATTERNS+=("${line%/}")
    done < "$GITIGNORE"
  fi

  should_keep() {
    local path="$1"
    for p in "${KEEP_PATTERNS[@]}"; do
      if [[ "$p" == /* ]]; then
        local rel="${path#$INSTALL_ROOT}"
        [[ "$rel" == "$p"* ]] && return 0
      else
        [[ "$path" == *"/$p"* || "$(basename "$path")" == "$p" ]] && return 0
      fi
    done
    return 1
  }

  echo "→ Wiping installed skills at $INSTALL_ROOT (gitignore-respecting)"
  deleted=0
  kept=0
  for entry in "$INSTALL_ROOT"/*; do
    [[ -d "$entry" ]] || continue
    name="$(basename "$entry")"
    if should_keep "$entry"; then
      echo "  ⊘ keep   $name  (matches .gitignore)"
      kept=$((kept + 1))
      continue
    fi
    if $DRY_RUN; then
      echo "  ~ dry-run delete $name"
    else
      rm -rf -- "$entry"
      echo "  ✗ delete $name"
    fi
    deleted=$((deleted + 1))
  done
  echo
  echo "→ Removed $deleted skill(s), kept $kept"
  echo
else
  echo "→ No installed skills at $INSTALL_ROOT, nothing to wipe"
  echo
fi

# ---- Regenerate lockfile so it reflects registry.json
if [[ -f "$LOCKFILE" ]]; then
  if $DRY_RUN; then
    echo "→ (dry-run) would remove $LOCKFILE"
  else
    rm -f "$LOCKFILE"
    echo "→ Removed $LOCKFILE"
  fi
fi
echo

# ---- Install everything from registry.json
if [[ ! -f "$REGISTRY" ]]; then
  echo "ERROR: registry not found at $REGISTRY" >&2
  exit 1
fi

echo "→ Registry: $REGISTRY"
echo

PYTHON_RUNNER="$(cat <<PYEOF
import json, subprocess, sys

REGISTRY = "$REGISTRY"
DRY_RUN = "$(echo $DRY_RUN)" == "true"

with open(REGISTRY) as f:
    reg = json.load(f)

skills = reg["skills"]
print(f"→ Found {len(skills)} skills")
print()

installed = 0
failed = 0

for s in skills:
    name = s["name"]
    owner = s["owner"]
    repo = s["repo"]

    cmd = ["npx", "skills", "add", f"https://github.com/{owner}/{repo}", "--skill", name, "-y"]
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
print(f"Done. installed={installed} failed={failed}")
sys.exit(0 if failed == 0 else 1)
PYEOF
)"

python3 -c "$PYTHON_RUNNER"
