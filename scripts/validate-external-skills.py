#!/usr/bin/env python3
"""Validate external-skills.yaml consistency with docs/migration-npx.md."""
from __future__ import annotations
import sys
from pathlib import Path
import yaml
import re

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    external = yaml.safe_load((ROOT / "external-skills.yaml").read_text())
    migration = (ROOT / "docs/migration-npx.md").read_text()

    errors = 0
    declared = set()
    for source in external.get("sources", []):
        for skill in source.get("selection", []):
            declared.add(skill)

    # Check each declared skill appears in migration doc
    for skill in sorted(declared):
        if skill not in migration:
            print(f"ERROR: {skill} declared in external-skills.yaml but missing from docs/migration-npx.md")
            errors += 1

    # Check total count
    local = sum(1 for s in external.get("maintained_locally", []) for _ in s.get("selection", []))
    total = len(declared) + local
    expected = f"{total} skills installed in total"
    if expected not in migration:
        print(f"ERROR: docs/migration-npx.md should state '{expected}'")
        errors += 1

    # Check --force not referenced
    if "--force" in migration:
        idx = migration.index("--force")
        context = migration[max(0, idx-50):idx+50]
        if "add" in context:
            print("ERROR: docs/migration-npx.md references --force which is not a valid add flag")
            errors += 1

    if errors:
        print(f"\n{errors} error(s) found")
        return 1
    print("external-skills.yaml is consistent with docs/migration-npx.md")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
