#!/usr/bin/env python3
"""Render the declared required and optional skill dependency graph."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

import yaml


GENERATED_NOTICE = "<!-- Generated from skills-manifest.yaml; do not edit manually. -->"


def mermaid_identifier(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def render_dependency_graph(manifest: dict[str, object]) -> str:
    entries = sorted(
        (
            entry
            for entry in manifest.get("skills", [])
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        ),
        key=lambda entry: entry["name"],
    )
    lines = [
        GENERATED_NOTICE,
        "",
        "# Skill dependency graph",
        "",
        "Solid edges are required installation dependencies. Dashed edges are optional workflow integrations. Informational references are omitted.",
        "",
        "```mermaid",
        "flowchart LR",
    ]

    connected_names: set[str] = set()
    edges: list[str] = []
    for entry in entries:
        name = str(entry["name"])
        source = mermaid_identifier(name)
        for dependency in sorted(
            item for item in entry.get("requires_skills", []) if isinstance(item, str)
        ):
            connected_names.update((name, dependency))
            edges.append(
                f"  {source} -->|requires| {mermaid_identifier(dependency)}"
            )
        for dependency in sorted(
            item for item in entry.get("optional_skills", []) if isinstance(item, str)
        ):
            connected_names.update((name, dependency))
            edges.append(
                f"  {source} -. optional .-> {mermaid_identifier(dependency)}"
            )

    for name in sorted(connected_names):
        lines.append(f'  {mermaid_identifier(name)}["{name}"]')
    lines.extend(sorted(edges))
    lines.extend(
        [
            "```",
            "",
            "## Declared dependencies",
            "",
            "| Skill | Required | Optional |",
            "|---|---|---|",
        ]
    )
    for entry in entries:
        required = ", ".join(f"`{item}`" for item in entry.get("requires_skills", [])) or "—"
        optional = ", ".join(f"`{item}`" for item in entry.get("optional_skills", [])) or "—"
        lines.append(f"| {entry['name']} | {required} | {optional} |")
    return "\n".join(lines) + "\n"


def render_legacy_graph_pointer() -> str:
    return "\n".join(
        [
            GENERATED_NOTICE,
            "",
            "# Skill dependency graph",
            "",
            "The canonical generated graph is [dependency-graph.md](dependency-graph.md).",
            "",
        ]
    )


def update_file(path: Path, content: str, check: bool) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return True
    if check:
        print(f"generated file is stale: {path}", file=sys.stderr)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def load_manifest(path: Path) -> dict[str, object]:
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("skills"), list):
        raise ValueError("skills must be a list")
    if any(
        not isinstance(entry, dict) or not isinstance(entry.get("name"), str)
        for entry in manifest["skills"]
    ):
        raise ValueError("each skill needs a string name")
    for entry in manifest["skills"]:
        for field in ("requires_skills", "optional_skills"):
            value = entry.get(field, [])
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"{entry['name']}.{field} must be a list of strings")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    try:
        manifest = load_manifest(root / "skills-manifest.yaml")
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"invalid manifest: {str(error).splitlines()[0]}", file=sys.stderr)
        return 2
    try:
        graph_content = render_dependency_graph(manifest)
        pointer_content = render_legacy_graph_pointer()
    except (KeyError, TypeError, ValueError) as error:
        print(f"invalid manifest: cannot render: {error}", file=sys.stderr)
        return 2
    generated = root / "docs" / "generated"
    results = [
        update_file(
            generated / "dependency-graph.md",
            graph_content,
            arguments.check,
        ),
        update_file(
            generated / "skill-dependency-graph.md",
            pointer_content,
            arguments.check,
        ),
    ]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
