#!/usr/bin/env bash
# reinstall.sh — Delete locally installed skills (respecting .gitignore) then
# reinstall everything declared in registry.json via ./install.sh.
#
# Idempotent: safe to re-run after editing registry.json.
#
# Layout (matches what `npx skills add` produces in this project):
#   ~/.agents/skills/.agents/skills/<skill-name>/   ← skill directories live here
#
# Skills whose path matches an entry in .gitignore are skipped on purpose
# (they are internal/custom, not part of the public distribution).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_SH="$REPO_DIR/install.sh"
GITIGNORE="$REPO_DIR/.gitignore"
INSTALL_ROOT="$HOME/.agents/skills/.agents/skills"

if [[ ! -d "$INSTALL_ROOT" ]]; then
  echo "→ No installed skills at $INSTALL_ROOT, nothing to delete"
  exit 0
fi

# Build a bash function from .gitignore that returns 0 if a path should be skipped.
# We only care about anchored entries (`/foo/` and `/foo`) plus bare names — those
# are the patterns that identify folders whose contents must be preserved.
declare -a KEEP_PATTERNS
while IFS= read -r raw; do
  # strip comments + blanks
  line="${raw%%#*}"
  line="$(echo "$line" | xargs || true)"
  [[ -z "$line" ]] && continue
  # strip trailing slash for matching
  KEEP_PATTERNS+=("${line%/}")
done < "$GITIGNORE"

should_keep() {
  local path="$1"
  for p in "${KEEP_PATTERNS[@]}"; do
    # anchored pattern (starts with '/') — match against absolute install root
    if [[ "$p" == /* ]]; then
      local rel="${path#$INSTALL_ROOT}"
      if [[ "$rel" == "$p"* ]]; then
        return 0
      fi
    else
      # bare pattern — match against any segment
      if [[ "$path" == *"/$p"* || "$(basename "$path")" == "$p" ]]; then
        return 0
      fi
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
  rm -rf -- "$entry"
  echo "  ✗ delete $name"
  deleted=$((deleted + 1))
done

echo
echo "→ Removed $deleted skill(s), kept $kept"
echo

# Also blow away the lockfile so install.sh writes a fresh one matching registry.json
rm -f "$REPO_DIR/skills-lock.json"
echo "→ Removed $REPO_DIR/skills-lock.json"
echo

# Now reinstall everything from registry.json
echo "→ Reinstalling from registry.json"
echo
bash "$INSTALL_SH"
