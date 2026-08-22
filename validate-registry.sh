#!/usr/bin/env bash
# validate-registry.sh — Sanity checks for registry.json.
#
# Catches:
# - count != skills.length
# - duplicate entries (name + owner + repo)
# - missing fields on each entry
# - invalid role values
# - empty name/owner/repo
#
# Exit code 0 = clean, 1 = at least one failure.

set -uo pipefail

REGISTRY="${1:-registry.json}"

if [[ ! -f "$REGISTRY" ]]; then
  echo "ERROR: $REGISTRY not found" >&2
  exit 2
fi

python3 - "$REGISTRY" <<'PYEOF'
import json, sys

path = sys.argv[1]
with open(path) as f:
    reg = json.load(f)

errors = []
warnings = []

count = reg.get("count", 0)
skills = reg.get("skills", [])

# 0) Global invariants
for key in ("name", "description", "version"):
    val = reg.get(key, "")
    if not val or not str(val).strip():
        errors.append(f"missing non-empty top-level '{key}'")
if not isinstance(count, int) or isinstance(count, bool):
    errors.append(f"'count' must be an integer, got {type(count).__name__}")
if not isinstance(skills, list):
    errors.append(f"'skills' must be an array, got {type(skills).__name__}")
import re as _re
ga = reg.get("generated_at", "")
if not _re.fullmatch(r"\d{4}-\d{2}-\d{2}", ga):
    errors.append(f"generated_at must be YYYY-MM-DD, got {ga!r}")

# 1) count == len(skills)
if isinstance(count, int) and count != len(skills):
    errors.append(f"count ({count}) != skills.length ({len(skills)})")

# 2) Each entry has required fields and a valid role
VALID_ROLES = {"discovery", "design", "implementation", "quality", "delivery", "style", "setup"}
seen_sources = set()  # (owner, repo, name) — exact source identity
seen_names = set()     # name only — namespace collision guard
for i, s in enumerate(skills):
    name = s.get("name", "").strip()
    owner = s.get("owner", "").strip()
    repo = s.get("repo", "").strip()
    role = s.get("role", "").strip()

    if not name:
        errors.append(f"skills[{i}]: missing 'name'")
        continue
    if not owner:
        errors.append(f"skills[{i}] ({name}): missing 'owner'")
    if not repo:
        errors.append(f"skills[{i}] ({name}): missing 'repo'")

    # TBD is not a valid upstream — a real owner/repo is mandatory.
    # Every registry entry must map to an installable GitHub source.
    if name.upper() == "TBD":
        errors.append(f"skills[{i}] ({name}): name must not be TBD")
    if owner.upper() == "TBD":
        errors.append(f"skills[{i}] ({name}): owner must not be TBD")
    if repo.upper() == "TBD":
        errors.append(f"skills[{i}] ({name}): repo must not be TBD")

    # Role is part of the contract — fail CI if missing or invalid
    if not role:
        errors.append(f"skills[{i}] ({name}): missing required 'role' field")
    elif role not in VALID_ROLES:
        errors.append(f"skills[{i}] ({name}): invalid role '{role}' (allowed: {sorted(VALID_ROLES)})")

    # Name uniqueness across the registry — protects against namespace
    # collisions when two repos publish a skill with the same name.
    if name in seen_names:
        errors.append(f"skills[{i}] ({name}): duplicate skill name (would collide on install)")
    seen_names.add(name)

    # Source identity — exact triple match for fork detection
    source_key = (owner, repo, name)
    if source_key in seen_sources:
        errors.append(f"skills[{i}] ({name}): duplicate source ({owner}/{repo}/{name})")
    seen_sources.add(source_key)

# 3) Skills must be sorted alphabetically by name (case-insensitive)
names = [s.get("name", "").strip() for s in skills]
if names != sorted(names, key=str.casefold):
    errors.append("skills must be sorted alphabetically by name")

# 4) Role distribution sanity check — roles never used are flagged as warnings
from collections import Counter
roles = Counter(s.get("role") for s in skills if s.get("role"))
unused_roles = VALID_ROLES - set(roles.keys())
if unused_roles:
    warnings.append(f"roles declared but unused: {sorted(unused_roles)}")

# Report
print(f"Registry: {path}")
print(f"  count: {count}")
print(f"  skills: {len(skills)}")
print(f"  roles: {dict(roles)}")
print()

if warnings:
    print("WARNINGS:")
    for w in warnings:
        print(f"  ⚠ {w}")
    print()

if errors:
    print("ERRORS:")
    for e in errors:
        print(f"  ✗ {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1)
else:
    print(f"✓ OK — {len(warnings)} warning(s)")
    sys.exit(0)
PYEOF
