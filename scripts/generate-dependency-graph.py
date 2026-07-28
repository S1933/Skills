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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    manifest = yaml.safe_load((root / "skills-manifest.yaml").read_text(encoding="utf-8"))
    generated = root / "docs" / "generated"
    results = [
        update_file(
            generated / "dependency-graph.md",
            render_dependency_graph(manifest),
            arguments.check,
        ),
        update_file(
            generated / "skill-dependency-graph.md",
            render_legacy_graph_pointer(),
            arguments.check,
        ),
    ]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
