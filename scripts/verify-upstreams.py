#!/usr/bin/env python3
"""Verify every registry skill is reachable upstream.

Resolves each skill through the GitHub recursive git tree, then matches the
skill's frontmatter `name:` — not its directory name. No upstream layout is
assumed: any `path/.../SKILL.md` is a candidate regardless of nesting depth.

Reachability only. Drift (content changes) is handled separately by
check-upstream-drift.py.

Usage:
    python3 scripts/verify-upstreams.py registry.json
    python3 scripts/verify-upstreams.py registry.json --baseline reviewed-upstreams.json
"""

import datetime
import json
import os
import sys
import urllib.request
import urllib.error

GH_TOKEN = os.environ.get("GH_TOKEN", "")

USER_AGENT = "s1933-skills-registry/1.1"


def api_get(url, accept="application/vnd.github+json"):
    """GET a GitHub API URL. Returns (status, bytes)."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
    }
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return 0, str(e).encode()


def default_branch(owner, repo):
    """Return the repo's default branch from the repo metadata."""
    status, body = api_get(f"https://api.github.com/repos/{owner}/{repo}")
    if status == 200:
        try:
            return json.loads(body).get("default_branch") or "main"
        except Exception:
            pass
    return "main"


def recursive_tree(owner, repo, branch):
    """Return (paths, sha_by_path) from the recursive git tree."""
    status, body = api_get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    )
    if status != 200:
        return None, {}
    try:
        tree = json.loads(body).get("tree", [])
    except Exception:
        return None, {}
    paths = [
        entry["path"]
        for entry in tree
        if entry.get("type") == "blob"
    ]
    sha_by_path = {
        entry["path"]: entry.get("sha")
        for entry in tree
        if entry.get("type") == "blob" and entry.get("sha")
    }
    return paths, sha_by_path


def skill_md_paths(paths):
    """All blob paths that end in /SKILL.md or equal SKILL.md."""
    return [
        path
        for path in paths
        if path == "SKILL.md" or path.endswith("/SKILL.md")
    ]


def frontmatter_name(raw):
    """Extract the YAML frontmatter `name:` field from a SKILL.md body.

    Returns None if there is no valid frontmatter `name`.
    """
    text = raw.decode("utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    # lines[0] == '---'; look for the closing '---'
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None
    for line in lines[1:end]:
        if line.lower().startswith("name:"):
            value = line.split(":", 1)[1].strip().strip("\"'")
            if value:
                return value
    return None


def build_upstream_index(owner, repo):
    """Map every upstream skill name -> {path, blob_sha} for one repo.

    Returns (index, duplicates, error).
    index:      {name: {path, blob_sha}} — first occurrence wins. Upstream
                repos often mirror a skill into several directories (e.g.
                plugins/<x>/skills/ and skills/); copies with identical
                content are treated as one skill.
    duplicates: {name: [paths]} only for genuinely ambiguous names — same
                frontmatter name, DIFFERENT blob content
    error:      None or a string describing a hard failure
    """
    branch = default_branch(owner, repo)
    paths, sha_by_path = recursive_tree(owner, repo, branch)
    if paths is None:
        return {}, {}, f"cannot fetch recursive tree for {owner}/{repo}"

    entries_by_name = {}
    for path in skill_md_paths(paths):
        sha = sha_by_path.get(path)
        if not sha:
            continue
        s, data = api_get(
            f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}",
            accept="application/vnd.github.raw+json",
        )
        if s != 200:
            continue
        name = frontmatter_name(data)
        if not name:
            continue
        entries_by_name.setdefault(name, []).append((path, sha))

    index = {
        name: {"path": entries[0][0], "blob_sha": entries[0][1]}
        for name, entries in entries_by_name.items()
    }
    duplicates = {
        name: [p for p, _ in entries]
        for name, entries in entries_by_name.items()
        if len({sha for _, sha in entries}) > 1
    }
    return index, duplicates, None


def main():
    args = sys.argv[1:]
    baseline_path = None
    if "--baseline" in args:
        i = args.index("--baseline")
        if i + 1 >= len(args):
            print("--baseline requires a path", file=sys.stderr)
            return 2
        baseline_path = args[i + 1]
        del args[i:i + 2]
    if not args:
        print("usage: verify-upstreams.py registry.json [--baseline PATH]",
              file=sys.stderr)
        return 2
    with open(args[0]) as f:
        reg = json.load(f)
    skills = reg["skills"]

    # Group skills by (owner, repo).
    from collections import defaultdict
    sources = defaultdict(list)
    for s in skills:
        sources[(s["owner"], s["repo"])].append(s["name"])

    checked = 0
    missing = []
    ambiguous = []  # registry skills whose upstream name matches multiple SKILL.md files
    baseline_sources = {}

    for (owner, repo), names in sorted(sources.items()):
        print(f"Checking {owner}/{repo}")
        index, duplicates, error = build_upstream_index(owner, repo)
        if error:
            print(f"  ✗ {error}")
            for name in names:
                missing.append((name, f"{owner}/{repo}"))
            continue
        found = []
        for name in names:
            checked += 1
            if name in index:
                found.append(name)
                print(f"  ✓ {name}")
                if name in duplicates:
                    ambiguous.append((name, f"{owner}/{repo}", duplicates[name]))
                baseline_sources.setdefault(f"{owner}/{repo}", {"skills": {}})[
                    "skills"][name] = index[name]
            else:
                print(f"  ✗ {name}")
                missing.append((name, f"{owner}/{repo}"))
        print(f"  {len(found)}/{len(names)}")

    print()
    print("Checked:")
    print(f"  repositories: {len(sources)}")
    print(f"  skills:       {checked}")
    print()

    status = 0
    if ambiguous:
        status = 1
        print("✗ Ambiguous upstream skill names (registry skill matches"
              " multiple upstream SKILL.md files):")
        for name, src, paths in sorted(ambiguous):
            print(f"  {name}  (upstream: {src})")
            for p in paths:
                print(f"    {p}")
        print()

    if missing:
        status = 1
        print("✗ Missing skills:")
        for name, src in missing:
            print(f"  {name}")
            print(f"    upstream: {src}")
        print()

    if baseline_path and status == 0:
        baseline = {
            "generated_at": datetime.date.today().isoformat(),
            "note": "Baseline of reviewed upstream blob SHAs, written by"
            " scripts/verify-upstreams.py --baseline. Refresh deliberately:"
            " review upstream changes, re-run with --baseline, then commit.",
            "sources": dict(sorted(baseline_sources.items())),
        }
        with open(baseline_path, "w") as f:
            json.dump(baseline, f, indent=2)
            f.write("\n")
        print(f"✓ Baseline written to {baseline_path}")

    if status == 0:
        print(f"✓ All {checked} upstream skills found.")
    return status


if __name__ == "__main__":
    sys.exit(main())