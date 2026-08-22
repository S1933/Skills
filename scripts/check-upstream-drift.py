#!/usr/bin/env python3
"""Detect whether any selected skill changed upstream since it was last reviewed.

Drift-only. Reachability (does the skill still exist at all) is handled by
verify-upstreams.py — a skill that disappeared is a HARD FAIL there, not a
"review required" here.

The comparison uses the blob SHA of each upstream SKILL.md, recorded in
reviewed-upstreams.json at the last explicit human review. This script NEVER
writes reviewed-upstreams.json: accepting a new upstream version is a
deliberate, human action (refresh the reviewed file, then commit).

Usage:
    python3 scripts/check-upstream-drift.py registry.json [reviewed-upstreams.json]
"""

import json
import os
import sys

# allow `python3 scripts/check-upstream-drift.py` from the repo root to import
# verify-upstreams.py (hyphenated filename, so load it explicitly).
import importlib.util
_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("verify_upstreams", os.path.join(_HERE, "verify-upstreams.py"))
vu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vu)

DEFAULT_REVIEWED = "reviewed-upstreams.json"


def load_json(path):
    with open(path) as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2:
        print("usage: check-upstream-drift.py registry.json [reviewed-upstreams.json]",
              file=sys.stderr)
        return 2
    registry_path = sys.argv[1]
    reviewed_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_REVIEWED

    reg = load_json(registry_path)
    if not os.path.exists(reviewed_path):
        print(f"No reviewed-upstreams.json at {reviewed_path} — nothing to compare."
              "\nRun verify-upstreams.py to establish a baseline, then commit it "
              "as the reviewed state.")
        return 1

    reviewed = load_json(reviewed_path)
    reviewed_sources = reviewed.get("sources", {})

    # Group current registry skills by (owner, repo).
    from collections import defaultdict
    current = defaultdict(list)
    for s in reg["skills"]:
        current[(s["owner"], s["repo"])].append(s["name"])

    changed = {}       # (owner,repo) -> [names changed]
    new_skill = {}     # (owner,repo) -> [names newly added, not in reviewed]
    removed = {}       # (owner,repo) -> [names removed from registry]
    unreviewed_repos = []

    for (owner, repo), names in sorted(current.items()):
        key = f"{owner}/{repo}"
        rev = reviewed_sources.get(key) or {}

        # Names present in the registry but never reviewed for this repo.
        rev_skills = rev.get("skills") or {}
        unknown = [n for n in names if n not in rev_skills]
        if not rev_skills and unknown:
            # Whole repo was never reviewed (e.g. freshly added).
            unreviewed_repos.append(key)
            continue
        if unknown:
            new_skill[key] = unknown

        # Fetch current blob SHAs for the skills of this repo.
        index, _, error = vu.build_upstream_index(owner, repo)
        if error:
            print(f"✗ {key}: {error}")
            continue
        for name in names:
            prev = rev_skills.get(name)
            if prev is None:
                continue
            cur = index.get(name)
            if cur is None:
                # Skill vanished upstream — verify-upstreams treats this as a
                # hard fail; surface it here as drift too for completeness.
                changed.setdefault(key, []).append((name, "REMOVED"))
            elif cur["blob_sha"] != prev.get("blob_sha"):
                changed.setdefault(key, []).append((name, "CHANGED"))

    # Report
    had_issue = False
    print("Upstream drift check against", reviewed_path)
    print()

    if unreviewed_repos:
        had_issue = True
        print("✗ Never reviewed (no baseline):")
        for key in sorted(unreviewed_repos):
            print(f"  {key}")

    if new_skill:
        had_issue = True
        print("✗ Newly added, not yet reviewed:")
        for key, names in sorted(new_skill.items()):
            print(f"  {key}: {', '.join(names)}")

    if changed:
        had_issue = True
        print("~ Upstream drift (review required):")
        for key, items in sorted(changed.items()):
            for name, kind in items:
                print(f"  {key}  ~ {name}  ({kind})")

    if not had_issue:
        print("✓ No upstream drift detected.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())