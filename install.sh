#!/usr/bin/env bash
# install.sh — Install all skills listed in registry.json via 'npx skills add'.
#
# Usage:
#   ./install.sh                  # install everything (skip TBD entries by default)
#   ./install.sh --all            # also attempt TBD entries (will warn/error)
#   ./install.sh --dry-run        # show what would run, don't execute
#   ./install.sh --only <name>    # install a single skill by name
#
# Replaces the old model of versioning SKILL.md content with declarative
# installation from skills.sh manifests.

set -euo pipefail

REGISTRY="${REGISTRY:-$(dirname "$0")/registry.json}"
DRY_RUN=false
ALL=false
ONLY=""

for arg in "$@"; do
  case "$arg" in
    --dry-run)   DRY_RUN=true ;;
    --all)       ALL=true ;;
    --only=*)    ONLY="${arg#--only=}" ;;
    --only)      shift; ONLY="${1:-}" ;;
    -h|--help)
      sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $arg" >&2; exit 2 ;;
  esac
done

if [[ ! -f "$REGISTRY" ]]; then
  echo "ERROR: registry not found at $REGISTRY" >&2
  exit 1
fi

# Parse JSON with python (always available with skills CLI) — no jq dependency
skills_count=$(python3 -c "import json,sys; d=json.load(open('$REGISTRY')); print(d['count'])")
echo "→ Found $skills_count skills in $REGISTRY"
echo

installed=0
skipped=0
failed=0

while IFS=$'\t' read -r name owner repo source; do
  if [[ -n "$ONLY" && "$name" != "$ONLY" ]]; then
    continue
  fi

  if [[ "$owner" == "TBD" ]]; then
    if [[ "$ALL" == true ]]; then
      echo "⚠ $name — TBD upstream, attempting anyway"
    else
      echo "⊘ $name — TBD upstream, skipped (use --all to attempt)"
      skipped=$((skipped+1))
      continue
    fi
  fi

  cmd="npx skills add https://github.com/$owner/$repo --skill $name"
  echo "+ $cmd"

  if [[ "$DRY_RUN" == true ]]; then
    echo "  (dry-run: skipped)"
    continue
  fi

  if npx skills add "https://github.com/$owner/$repo" --skill "$name" >/dev/null 2>&1; then
    echo "  ✓ installed"
    installed=$((installed+1))
  else
    echo "  ✗ failed"
    failed=$((failed+1))
  fi
done < <(python3 -c "
import json, sys
with open('$REGISTRY') as f:
    d = json.load(f)
for s in d['skills']:
    src = s.get('source', '')
    print(f\"{s['name']}\t{s['owner']}\t{s['repo']}\t{src}\")
")

echo
echo "Done. installed=$installed skipped=$skipped failed=$failed"
[[ $failed -eq 0 ]] || exit 1
