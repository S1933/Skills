#!/usr/bin/env python3
"""Validate external-skills.yaml consistency with docs/migration-npx.md.

Strengthened per CodeRabbit review:
- Parses every ```bash code block that runs an `npx ... skills@latest add`
  command, rather than substring-searching the whole Markdown file.
- Verifies source / agent / skill mappings structurally against
  external-skills.yaml (declarations ↔ install blocks).
- Scans every --force occurrence, not just the first.

The doc may reference removed/legacy skills in prose or in `remove` blocks
without invalidating the validator.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DOC = ROOT / "docs" / "migration-npx.md"
EXTERNAL_YAML = ROOT / "external-skills.yaml"

# Match a fenced ```bash ... ``` block. The regex is non-greedy and allows
# the closing fence to be anywhere on its own line.
FENCED_BASH_RE = re.compile(
    r"```bash\s*\n(.*?)\n```",
    re.DOTALL,
)

# Match an `npx ... skills@latest add <source> ...` command line. We pull
# out the source repo, the --agent flag(s), and the --skill flags.
# Notes on shape:
#   - The line may be wrapped with `\` continuations and end with `; \`.
#   - There may be a `for agent in $AGENTS; do \` opener and a `done` closer.
#   - A block can contain a single command (e.g. for ksimback) or a loop.
ADD_CMD_RE = re.compile(
    r"npx\s+--yes\s+skills@latest\s+add\s+(?P<source>[\w./-]+)"
)

AGENT_LITERAL_RE = re.compile(r"--agent\s+(\S+)")
SKILL_RE = re.compile(r"--skill\s+([\w.-]+)")


@dataclass
class AddBlock:
    """A single ```bash block containing one or more `add` commands."""

    source: str
    # Hard-coded --agent values (e.g. "--agent claude-code"). Empty if the
    # block uses the `for agent in $AGENTS` shell loop.
    literal_agents: list[str] = field(default_factory=list)
    # Skills installed by this block.
    skills: list[str] = field(default_factory=list)
    # True if the block uses `for agent in $AGENTS` (or similar loop). When
    # true, the per-block agent reach is the AGENTS set defined at the top
    # of the doc.
    uses_agent_loop: bool = False
    block_index: int = 0


@dataclass
class SourceDecl:
    """A source entry from external-skills.yaml."""

    name: str
    skills: list[str]
    agents: list[str]
    claude_code_only: bool


def load_source_decls() -> list[SourceDecl]:
    """Read the sources + maintained_locally entries from external-skills.yaml.

    Both sections describe installable selections. `sources` use a `name:`
    key; `maintained_locally` entries use `source:`. From the validator's
    perspective, both must have install blocks in the doc.
    """
    data = yaml.safe_load(EXTERNAL_YAML.read_text())
    decls: list[SourceDecl] = []
    for key in ("sources", "maintained_locally"):
        for source in data.get(key, []):
            name = source.get("name") or source.get("source")
            if not name:
                continue
            decls.append(
                SourceDecl(
                    name=name,
                    skills=list(source.get("selection", [])),
                    agents=list(source.get("agents", [])),
                    claude_code_only=bool(source.get("claude_code_only", False)),
                )
            )
    return decls


def parse_doc_agent_set(doc: str) -> set[str]:
    """Return the AGENTS set defined in the doc (e.g. {'claude-code', 'codex', ...})."""
    m = re.search(r'AGENTS\s*=\s*"([^"]+)"', doc)
    if not m:
        return set()
    return set(m.group(1).split())


def parse_add_blocks(doc: str) -> list[AddBlock]:
    """Walk every ```bash block and extract its `add` command(s)."""
    blocks: list[AddBlock] = []
    for idx, fence in enumerate(FENCED_BASH_RE.finditer(doc)):
        body = fence.group(1)
        if "npx" not in body or "skills@latest add" not in body:
            continue
        cmd_match = ADD_CMD_RE.search(body)
        if not cmd_match:
            continue
        source = cmd_match.group("source")
        block = AddBlock(source=source, block_index=idx)
        # Detect the `for agent in $AGENTS` shell loop pattern.
        block.uses_agent_loop = bool(re.search(r"for\s+agent\s+in\s+\$AGENTS", body))
        # Collect literal --agent values, ignoring the loop-variable form
        # `--agent "$agent"`.
        for m in AGENT_LITERAL_RE.finditer(body):
            value = m.group(1).strip('"').strip("'")
            if value.startswith("$"):
                continue
            block.literal_agents.append(value)
        # Collect skills (deduped, order-preserving).
        seen: set[str] = set()
        for m in SKILL_RE.finditer(body):
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                block.skills.append(name)
        blocks.append(block)
    return blocks


def report(errors: list[str], msg: str) -> None:
    errors.append(msg)
    print(f"ERROR: {msg}")


def main() -> int:
    doc = MIGRATION_DOC.read_text()
    decls = load_source_decls()
    doc_agents = parse_doc_agent_set(doc)
    add_blocks = parse_add_blocks(doc)

    # Index declarations by source name.
    decl_by_name: dict[str, SourceDecl] = {d.name: d for d in decls}

    # Group install blocks by source so we can union-skill-check.
    blocks_by_source: dict[str, list[AddBlock]] = defaultdict(list)
    for b in add_blocks:
        blocks_by_source[b.source].append(b)

    errors: list[str] = []

    # --- Check 1: every declared source has at least one install block. ---
    for decl in decls:
        if not blocks_by_source.get(decl.name):
            report(
                errors,
                f"source {decl.name!r} declared in external-skills.yaml has no "
                f"`npx skills@latest add` block in docs/migration-npx.md",
            )

    # --- Check 2: every install block maps to a declared source. ---
    for b in add_blocks:
        if b.source not in decl_by_name:
            report(
                errors,
                f"install block #{b.block_index} targets undeclared source "
                f"{b.source!r} (no entry in external-skills.yaml sources)",
            )

    # --- Check 3: per-source skill coverage and per-block agent mapping. ---
    for decl in decls:
        decl_skills = set(decl.skills)
        decl_agents = set(decl.agents)
        installed_skills: set[str] = set()
        for b in blocks_by_source.get(decl.name, []):
            # 3a. Agent reachability for this block.
            if b.uses_agent_loop:
                # The loop iterates over $AGENTS. The reachable set is the
                # intersection of the doc's AGENTS set with the source's
                # declared agents. If the source is claude_code_only, the
                # doc's AGENTS loop is a misconfiguration: it would target
                # agents the source doesn't support.
                if decl.claude_code_only and doc_agents:
                    extra = doc_agents - decl_agents
                    if extra:
                        report(
                            errors,
                            f"source {decl.name!r} is claude_code_only but its "
                            f"install block iterates $AGENTS which includes "
                            f"{sorted(extra)}; must be restricted to "
                            f"{sorted(decl_agents)}",
                        )
                # Skills added in a loop block still need each literal
                # --agent referenced (none here) to be in decl_agents.
            else:
                if not b.literal_agents:
                    report(
                        errors,
                        f"install block #{b.block_index} for {decl.name!r} has "
                        f"no --agent flag and no `$AGENTS` loop",
                    )
                for agent in b.literal_agents:
                    if agent not in decl_agents:
                        report(
                            errors,
                            f"install block #{b.block_index} for {decl.name!r} "
                            f"uses --agent {agent!r} which is not in the "
                            f"source's declared agents list "
                            f"({sorted(decl_agents)})",
                        )
            # 3b. Skills added must all be declared.
            for skill in b.skills:
                if skill not in decl_skills:
                    report(
                        errors,
                        f"install block #{b.block_index} for {decl.name!r} "
                        f"installs --skill {skill!r} which is not declared in "
                        f"external-skills.yaml",
                    )
                installed_skills.add(skill)
        # 3c. Every declared skill for this source must be installed.
        missing = decl_skills - installed_skills
        if missing:
            report(
                errors,
                f"source {decl.name!r} declares skills {sorted(missing)} but no "
                f"install block in docs/migration-npx.md adds them",
            )

    # --- Check 4: install-count prose in the doc must match the YAML. ---
    #
    # The doc's "Resulting selection" section is the human-readable summary
    # of the install plan. For a per-agent install, the count is:
    #   total_skills - skills whose source has claude_code_only=true
    # (for non-claude-code agents). For claude-code, every declared skill is
    # installed. We parse the prose for these three numbers and verify them.
    data = yaml.safe_load(EXTERNAL_YAML.read_text())
    decls_for_count = data.get("sources", []) + data.get("maintained_locally", [])
    declared_total = sum(
        len(s.get("selection", [])) for s in decls_for_count
    )
    claude_code_only_skill_count = sum(
        len(s.get("selection", []))
        for s in data.get("sources", [])
        if s.get("claude_code_only")
    )
    expected_claude = declared_total
    expected_other = declared_total - claude_code_only_skill_count

    # The doc states: "N skills installed for `claude-code`; M for `codex`,
    # `opencode`, and `cursor`". Extract N and M with a tolerant regex.
    prose_match = re.search(
        r"(\d+)\s+skills?\s+installed\s+for\s+`?claude-code`?\s*;\s*"
        r"(\d+)\s+for\s+`?codex`?",
        doc,
        re.IGNORECASE,
    )
    if not prose_match:
        report(
            errors,
            "docs/migration-npx.md should state the per-agent install counts "
            f"(e.g. '{expected_claude} skills installed for `claude-code`; "
            f"{expected_other} for `codex`, `opencode`, and `cursor`')",
        )
    else:
        doc_claude = int(prose_match.group(1))
        doc_other = int(prose_match.group(2))
        if doc_claude != expected_claude:
            report(
                errors,
                f"docs/migration-npx.md says {doc_claude} skills installed for "
                f"`claude-code` but external-skills.yaml declares "
                f"{expected_claude}",
            )
        if doc_other != expected_other:
            report(
                errors,
                f"docs/migration-npx.md says {doc_other} skills installed for "
                f"`codex` (and other non-claude agents) but external-skills.yaml "
                f"implies {expected_other} "
                f"({declared_total} declared - {claude_code_only_skill_count} "
                f"claude_code_only = {expected_other})",
            )

    # --- Check 5: scan EVERY --force occurrence, not just the first. ---
    for m in re.finditer(r"--force", doc):
        idx = m.start()
        # Look at a generous context window (the surrounding paragraph /
        # bash block) for a code-block `add` command.
        # We pick the nearest preceding ```bash fence and the next closing
        # ``` to bound the context.
        window_start = doc.rfind("```bash", 0, idx)
        if window_start == -1:
            # Prose mention of --force is allowed; only block usage is an
            # error. Skip prose hits.
            continue
        window_end = doc.find("```", idx)
        if window_end == -1:
            window_end = len(doc)
        context = doc[window_start:window_end]
        if "add" in context and "skills@latest add" in context:
            report(
                errors,
                f"docs/migration-npx.md uses --force inside an `add` block at "
                f"offset {idx} (--force is not a valid flag for "
                f"`npx skills add`; use --yes for confirmation)",
            )

    if errors:
        print(f"\n{len(errors)} error(s) found")
        return 1
    print(
        "external-skills.yaml is consistent with docs/migration-npx.md "
        f"({len(add_blocks)} install block(s) validated across "
        f"{len(decls)} source(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
