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

# 1) count == len(skills)
if count != len(skills):
    errors.append(f"count ({count}) != skills.length ({len(skills)})")

# 2) Each entry has required fields and a valid role
VALID_ROLES = {"discovery", "design", "implementation", "quality", "delivery", "style"}
seen = set()
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

    if owner == "TBD" or repo == "TBD":
        warnings.append(f"skills[{i}] ({name}): TBD upstream — install skipped by default")

    if role and role not in VALID_ROLES:
        errors.append(f"skills[{i}] ({name}): invalid role '{role}' (allowed: {sorted(VALID_ROLES)})")
    elif not role:
        warnings.append(f"skills[{i}] ({name}): no 'role' field")

    key = (owner, repo, name)
    if key in seen:
        errors.append(f"skills[{i}] ({name}): duplicate entry ({owner}/{repo}/{name})")
    seen.add(key)

# 3) Role distribution sanity check
from collections import Counter
roles = Counter(s.get("role", "(none)") for s in skills)
unbalanced = [r for r, n in roles.items() if n == 0]
if unbalanced and "(none)" not in unbalanced:
    warnings.append(f"unused roles: {unbalanced}")

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
