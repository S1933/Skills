#!/usr/bin/env python3
"""Generate the root README and detailed catalogue from the manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml


NOTICE = "<!-- Generated from skills-manifest.yaml; do not edit manually. -->"


def markdown_cell(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def entries(manifest: dict[str, object], visibility: str) -> list[dict[str, object]]:
    return sorted((entry for entry in manifest["skills"] if entry.get("visibility") == visibility), key=lambda entry: entry["name"])


def render_table(items: list[dict[str, object]]) -> list[str]:
    lines = ["| Skill | Invocation | Clients | Description |", "|---|---|---|---|"]
    for entry in items:
        path = entry["path"]
        clients = ", ".join(entry.get("clients", []))
        lines.append(
            f"| [`{markdown_cell(entry['name'])}`]({path}/) | "
            f"{markdown_cell(entry['invocation'])} | {markdown_cell(clients)} | "
            f"{markdown_cell(entry['description'])} |"
        )
    return lines


def render_readme(manifest: dict[str, object]) -> str:
    public = entries(manifest, "public")
    private = entries(manifest, "private")
    lines = [NOTICE, "", "# Skills catalogue", "", "A validated catalogue of portable and client-specific Agent Skills. The repository is in stabilization mode: improve existing skills and safety/evaluation coverage before proposing new functional skills.", "", "- [Installation](docs/installation.md)", "- [Authoring standard](docs/skill-authoring-standard.md)", "- [Contributing](CONTRIBUTING.md)", "- [Detailed generated catalogue](docs/generated/catalogue.md)", "- [Dependency graph](docs/generated/dependency-graph.md)", "- [Evaluation format](docs/evaluations.md)", "- [Provenance](NOTICE.md)", "", f"## Public skills ({len(public)})", ""]
    lines.extend(render_table(public))
    lines.extend(["", f"## Private/environment-specific skills ({len(private)})", "", "Private skills remain in the repository for local use but are excluded from public-only installation guidance and may require `.local/skills-environment.yaml`.", ""])
    lines.extend(render_table(private))
    lines.extend(["", "## Validate", "", "```bash", "python3 -m pip install -r requirements-dev.txt", "python3 -m unittest discover --start-directory tests --pattern 'test_*.py'", "python3 scripts/generate-catalogue.py --check", "python3 scripts/generate-dependency-graph.py --check", "python3 scripts/validate-evals.py", "python3 scripts/validate-skills.py", "git ls-files '*.sh' '*.zsh' | xargs shellcheck", "```", "", "See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for licensing and adapted upstream material.", ""])
    return "\n".join(lines)


def render_catalogue(manifest: dict[str, object]) -> str:
    lines = [NOTICE, "", "# Generated skill catalogue", ""]
    for visibility in ("public", "private"):
        lines.extend([f"## {visibility.title()} skills", ""])
        for entry in entries(manifest, visibility):
            required = ", ".join(entry.get("requires_skills", [])) or "none"
            optional = ", ".join(entry.get("optional_skills", [])) or "none"
            commands = ", ".join(entry.get("requires_commands", [])) or "none"
            lines.extend([f"### `{entry['name']}`", "", entry["description"], "", f"- Path: `{entry['path']}`", f"- Invocation: {entry['invocation']}", f"- Clients: {', '.join(entry.get('clients', []))}", f"- Required skills: {required}", f"- Optional skills: {optional}", f"- Commands: {commands}", f"- Compatibility: {entry.get('compatibility', 'not declared')}", f"- Main-file words: approximately {entry['approximate_word_count']}", ""])
    return "\n".join(lines)


def update(path: Path, content: str, check: bool) -> bool:
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
    for entry in manifest["skills"]:
        if not isinstance(entry, dict) or any(
            not isinstance(entry.get(field), str)
            for field in ("name", "path", "visibility", "invocation", "description")
        ):
            raise ValueError("each skill needs string name, path, visibility, invocation, and description")
        if not isinstance(entry.get("approximate_word_count"), int) or isinstance(entry.get("approximate_word_count"), bool):
            raise ValueError(f"{entry['name']}.approximate_word_count must be an integer")
        for field in ("clients", "requires_skills", "optional_skills", "requires_commands"):
            value = entry.get(field, [])
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"{entry['name']}.{field} must be a list of strings")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        manifest = load_manifest(root / "skills-manifest.yaml")
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"invalid manifest: {str(error).splitlines()[0]}", file=sys.stderr)
        return 2
    try:
        readme_content = render_readme(manifest)
        catalogue_content = render_catalogue(manifest)
    except (KeyError, TypeError, ValueError) as error:
        print(f"invalid manifest: cannot render: {error}", file=sys.stderr)
        return 2
    ok = update(root / "README.md", readme_content, args.check)
    ok = update(root / "docs/generated/catalogue.md", catalogue_content, args.check) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
