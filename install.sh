#!/usr/bin/env bash
# install.sh — Safely install every skill declared in registry.json.
#
# Hardened installer. Order:
#   1. preflight (tools + git repo present)
#   2. validate the registry (abort before touching the filesystem)
#   3. backup current public skills into a temp dir
#   4. install (one npx call per upstream, kept private skills preserved)
#   5. post-validate that every registry skill's <name>/SKILL.md exists
#   6. on ANY failure: roll back to the previous installation, then exit 1
#
# This repo IS the global skills directory: ~/.claude/skills is a symlink to
# ~/.agents/skills, which is this checkout. Skills install with 'skills add -g',
# whose global root is exactly ~/.agents/skills — the repo root.
#
# Usage:
#   ./install.sh            # wipe public skills + install everything, with rollback
#   ./install.sh --dry-run  # plan only, no filesystem changes

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
REGISTRY="${REGISTRY:-$REPO_ROOT/registry.json}"
INSTALL_ROOT="$REPO_ROOT"

# Pin the skills CLI so two runs of the same commit use the same version.
SKILLS_CLI_VERSION="${SKILLS_CLI_VERSION:-1.5.23}"

# Appended to across every upstream, so a failure keeps the earlier context.
INSTALL_LOG="${INSTALL_LOG:-/tmp/install-skills.log}"

DRY_RUN=false
case "${1:-}" in
  --dry-run)  DRY_RUN=true ;;
  -h|--help)  sed -n '2,18p' "$0"; exit 0 ;;
  "")         ;;
  *)
    echo "ERROR: unknown arg: $1" >&2
    echo "Usage: $0 [--dry-run]" >&2
    exit 2
    ;;
esac

say() { echo "$*"; }
die() { echo "ERROR: $*" >&2; exit 2; }

# ---- Phase 7: preflight ---------------------------------------------
preflight() {
  for tool in git python3 node npx; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      die "missing required tool: $tool"
    fi
  done
  if ! git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    die "not inside a git work tree: $REPO_ROOT"
  fi
}

# ---- Registry validation (abort before any filesystem change) -------
validate_registry() {
  if [[ ! -f "$REGISTRY" ]]; then
    die "registry not found at $REGISTRY"
  fi
  if [[ -f "$REPO_ROOT/validate-registry.sh" ]]; then
    "$REPO_ROOT/validate-registry.sh" "$REGISTRY" >/dev/null
    local rc=$?
    if [[ $rc -ne 0 ]]; then
      die "registry validation failed (exit $rc)"
    fi
  fi
}

# Runs the python with the registry on stdin; echoes the parsed JS.
python3_with_registry() {
  REGISTRY="$REGISTRY" python3 - "$1" <<'PYEOF'
import json, os, sys
reg = json.load(open(os.environ["REGISTRY"]))
path = sys.argv[1]
if path == "installs":
    # One command per upstream, skills grouped together.
    from collections import defaultdict
    groups = defaultdict(list)
    for s in reg["skills"]:
        groups[(s["owner"], s["repo"])].append(s["name"])
    for (owner, repo), names in sorted(groups.items()):
        print(f"{owner}/{repo}\t" + " ".join(names))
elif path == "names":
    for s in reg["skills"]:
        print(s["name"])
elif path == "count":
    print(len(reg["skills"]))
PYEOF
}

# ---- Phase 6: is this skill directory protected by .gitignore? -------
is_preserved() {
  git -C "$REPO_ROOT" check-ignore -q -- "$1"
}

wipe_public_skills() {
  local deleted=0 kept=0
  for entry in "$INSTALL_ROOT"/*; do
    [[ -d "$entry" ]] || continue
    [[ -f "$entry/SKILL.md" ]] || continue
    local name
    name="$(basename "$entry")"
    if is_preserved "$entry"; then
      say "  ⊘ keep   $name  (.gitignore)"
      kept=$((kept + 1))
      continue
    fi
    say "  ✗ delete $name"
    deleted=$((deleted + 1))
  done
  say "→ Removed $deleted public skill(s), kept $kept protected"
}

# ---- Phase 8: backup / rollback -------------------------------------
BACKUP_DIR=""
backup_public_skills() {
  BACKUP_DIR="$(mktemp -d)"
  for entry in "$INSTALL_ROOT"/*; do
    [[ -d "$entry" ]] || continue
    [[ -f "$entry/SKILL.md" ]] || continue
    if is_preserved "$entry"; then
      continue
    fi
    local name
    name="$(basename "$entry")"
    # mv is atomic and cheap; only copies across filesystems.
    mv -- "$entry" "$BACKUP_DIR/$name" 2>/dev/null \
      || cp -a -- "$entry" "$BACKUP_DIR/$name"
    say "  ⌛ backed up $name"
  done
}

delete_partial_installation() {
  for entry in "$INSTALL_ROOT"/*; do
    [[ -d "$entry" ]] || continue
    [[ -f "$entry/SKILL.md" ]] || continue
    if is_preserved "$entry"; then
      continue
    fi
    rm -rf -- "$entry"
  done
}

restore_backup() {
  if [[ -z "$BACKUP_DIR" ]]; then return; fi
  for entry in "$BACKUP_DIR"/*; do
    [[ -e "$entry" ]] || continue
    local name
    name="$(basename "$entry")"
    rm -rf -- "$INSTALL_ROOT/$name"
    mv -- "$entry" "$INSTALL_ROOT/$name"
    say "  ↺ restored $name"
  done
  rm -rf "$BACKUP_DIR"
  BACKUP_DIR=""
}

# ---- Phase 11+12: install, grouped per upstream, pinned CLI ----------
install_all() {
  : >"$INSTALL_LOG"
  while IFS=$'\t' read -r source names; do
    [[ -z "$source" ]] && continue
    local owner repo
    owner="${source%%/*}"
    repo="${source#*/}"
    say "+ npx skills@${SKILLS_CLI_VERSION} add ${owner}/${repo} --skill [${names// /, }]"
    if $DRY_RUN; then
      continue
    fi
    # Build a repeated --skill flag set.
    local add_args=()
    for n in $names; do
      add_args+=(--skill "$n")
    done
    # </dev/null is load-bearing: npx would otherwise inherit this loop's stdin
    # and drain the remaining upstreams from the process substitution.
    if ! npx --yes "skills@${SKILLS_CLI_VERSION}" add \
        "https://github.com/${owner}/${repo}" \
        "${add_args[@]}" -g -y </dev/null >>"$INSTALL_LOG" 2>&1; then
      say "  ✗ install failed for ${owner}/${repo} (see $INSTALL_LOG)"
      return 1
    fi
    say "  ✓ ${owner}/${repo}"
  done < <(python3_with_registry installs)
}

# ---- Phase 9: post-validation ---------------------------------------
validate_installed() {
  local expected=0 installed=0 missing=0
  local name
  while read -r name; do
    [[ -z "$name" ]] && continue
    expected=$((expected + 1))
    if [[ -f "$INSTALL_ROOT/$name/SKILL.md" ]]; then
      installed=$((installed + 1))
    else
      missing=$((missing + 1))
      say "  ✗ missing $name/SKILL.md"
    fi
  done < <(python3_with_registry names)

  say "Expected skills:  $expected"
  say "Installed skills: $installed"
  say "Missing:          $missing"
  [[ $missing -eq 0 ]] || return 1
  say "✓ Installation validated."
}

# ---------------------------------------------------------------------

preflight
validate_registry

if $DRY_RUN; then
  say "→ Registry: $REGISTRY"
  say "→ Dry-run: skills planned below, no filesystem changes."
  say ""
  python3_with_registry installs | while IFS=$'\t' read -r source names; do
    [[ -z "$source" ]] && continue
    say "  + ${source}  ->  [${names// /, }]"
  done
  say ""
  say "→ private skills preserved via .gitignore:"
  ls -d "$INSTALL_ROOT"/[REMOVED-INTERNAL-SKILL] "$INSTALL_ROOT"/[REMOVED-INTERNAL-SKILL] "$INSTALL_ROOT"/[REMOVED-INTERNAL-MARKER] \
      "$INSTALL_ROOT"/[REMOVED-INTERNAL-SKILL] "$INSTALL_ROOT"/[REMOVED-INTERNAL-SKILL] \
      "$INSTALL_ROOT"/[REMOVED-INTERNAL-SKILL] "$INSTALL_ROOT"/[REMOVED-INTERNAL-SKILL] 2>/dev/null \
    | sed "s|$INSTALL_ROOT/|  ⊘ |"
  exit 0
fi

say "→ Backing up current public skills"
backup_public_skills
say ""

if install_all; then
  say ""
  if validate_installed; then
    rm -rf "$BACKUP_DIR"
    BACKUP_DIR=""
    say "→ Installation complete and validated ($SKILLS_CLI_VERSION)."
    exit 0
  fi
fi

# ---- rollback -------------------------------------------------------
say ""
say "→ Installation failed. Rolling back."
delete_partial_installation
restore_backup
say "→ Previous installation restored."
exit 1