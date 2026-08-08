#!/usr/bin/env python3
"""Validate external-skills.yaml consistency with docs/migration-npx.md.

Strengthened per CodeRabbit review:
- Parses every ```bash code block that runs an `npx ... skills@latest add`
  command, rather than substring-searching the whole Markdown file.
- Verifies source / agent / skill mappings structurally against
  external-skills.yaml (declarations ↔ install blocks).
- Scans every --force occurrence, not just the first.
- Per-command parsing: each `npx skills@latest add` invocation in a fenced
  block becomes its own AddBlock with its own flags/agents/skills; flags
  and selections never bleed across commands.
- Union-based agent coverage: when a source is installed via several
  commands, the union of all commands' agent reach is what must cover
  the declared agent list. A single command may only target a subset.

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
#   - A block can contain MULTIPLE independent `npx skills@latest add`
#     commands on separate logical lines (e.g. for installs split across
#     agents for sources that have a mix of loop and literal installs).
ADD_CMD_RE = re.compile(
    r"npx\s+--yes\s+skills@latest\s+add\s+(?P<source>[\w./-]+)"
)

ADD_CMD_HEAD_RE = re.compile(r"npx\s+--yes\s+skills@latest\s+add\b")
AGENT_LITERAL_RE = re.compile(r"--agent\s+(\S+)")
SKILL_RE = re.compile(r"--skill\s+([\w.-]+)")
GLOBAL_FLAG_RE = re.compile(r"(?:^|\s)--global(?:\s|$)")
COPY_FLAG_RE = re.compile(r"(?:^|\s)--copy(?:\s|$)")


@dataclass
class AddBlock:
    """A single `npx skills@latest add` command (one per command, not per
    fenced block)."""

    source: str
    # Hard-coded --agent values (e.g. "--agent claude-code"). Empty if the
    # command uses the `for agent in $AGENTS` shell loop.
    literal_agents: list[str] = field(default_factory=list)
    # Skills installed by this command.
    skills: list[str] = field(default_factory=list)
    # True if the command uses `for agent in $AGENTS` (or similar loop).
    # When true, the per-command agent reach is the AGENTS set defined at
    # the top of the doc.
    uses_agent_loop: bool = False
    # True if this command carries the required --global flag.
    has_global_flag: bool = False
    # True if this command carries the required --copy flag.
    has_copy_flag: bool = False
    # Index of the parent fenced block, for error reporting.
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


def _is_for_loop_opener(text: str) -> bool:
    r"""True if the text is a `for ... in $AGENTS; do \` style opener or `do` line.

    These are preambles that must be folded into the following add command
    so per-command loop detection has the necessary context.
    """
    stripped = text.strip()
    if not stripped:
        return False
    if re.search(r"for\s+agent\s+in\s+\$AGENTS\b", stripped):
        return True
    if stripped in {"do", "do \\"}:
        return True
    if re.match(r"^do\s*\\?\s*$", stripped):
        return True
    return False


def _split_block_into_commands(body: str) -> list[str]:
    r"""Split a fenced block body into one chunk per `npx skills@latest add`.

    A block may contain several `add` commands (or `add` and `remove`, etc.)
    chained by shell `;` or by being on distinct logical lines. The output
    is a list of segments, one per `add` command, where the leading
    preamble (e.g. `for ... do`) is folded into the segment that follows
    it so per-command loop detection still works. Trailing `done` and
    empty segments are dropped.

    Splitting rules:
      1. Normalize line continuations (`\<newline>` -> space) so a wrapped
         `for ... do; \` chain reads as a single logical line.
      2. Split on shell `;` boundaries.
      3. Within each `;` segment, split on every fresh `npx ... skills@latest
         add` invocation so two distinct commands on separate lines become
         two distinct segments.
      4. Fold `for ... do` preambles into the next add command.
    """
    # Normalize line continuations: " \<newline>" -> " " so the block
    # reads as a single logical line per `;` segment.
    flat = re.sub(r"\\\s*\n", " ", body)
    # Split on shell `;` to get individual commands.
    semicolon_segments = [seg.strip() for seg in flat.split(";") if seg.strip()]

    # Within each `;` segment, split on a fresh `npx ... skills@latest add`.
    # Each "part" is either an add command or a non-add piece (e.g. the
    # body of a `remove` command, which we drop).
    raw_parts: list[str] = []
    for seg in semicolon_segments:
        cursor = 0
        for m in re.finditer(ADD_CMD_HEAD_RE, seg):
            if m.start() > cursor:
                # Text before the next add command (e.g. a `for ... do`
                # preamble, or trailing flags from the previous command)
                # becomes its own part.
                head = seg[cursor:m.start()].strip()
                if head:
                    raw_parts.append(head)
            # The add command's text is bounded by THIS `npx` and the
            # START of the next `npx` (if any). Without this `end` bound,
            # the prior implementation pulled the rest of the segment,
            # which fused subsequent commands into one block.
            end = m.end()
            nxt = ADD_CMD_HEAD_RE.search(seg, end)
            stop = nxt.start() if nxt else len(seg)
            raw_parts.append(seg[m.start():stop].strip())
            cursor = stop
        if cursor < len(seg):
            tail = seg[cursor:].strip()
            if tail:
                raw_parts.append(tail)

    # Fold `for ... do` preambles into the next add command so the
    # per-command loop marker is preserved. Trailing `done` and any
    # other non-add tail is dropped (it's noise for the validator).
    commands: list[str] = []
    pending_preamble: list[str] = []
    for part in raw_parts:
        if ADD_CMD_HEAD_RE.search(part):
            merged = " ".join(pending_preamble + [part])
            commands.append(merged)
            pending_preamble = []
        elif _is_for_loop_opener(part):
            # Loop opener belongs to the following add command.
            pending_preamble.append(part)
        else:
            # Non-add part that is neither a loop opener nor a fresh
            # add command. Examples: a `remove` command body, a trailing
            # `done`, etc. None of these affect the add-block accounting.
            continue
    return commands


def _extract_add_command(
    segment: str, fallback_source: str, block_index: int
) -> AddBlock | None:
    """Build an AddBlock from one logical command segment, or None if it
    is not an `npx skills@latest add` command (e.g. a `for` line)."""
    cmd_match = ADD_CMD_RE.search(segment)
    if not cmd_match:
        return None
    source = cmd_match.group("source") or fallback_source
    block = AddBlock(source=source, block_index=block_index)
    block.uses_agent_loop = bool(re.search(r"for\s+agent\s+in\s+\$AGENTS", segment))
    block.has_global_flag = bool(GLOBAL_FLAG_RE.search(segment))
    block.has_copy_flag = bool(COPY_FLAG_RE.search(segment))
    for m in AGENT_LITERAL_RE.finditer(segment):
        value = m.group(1).strip('"').strip("'")
        if value.startswith("$"):
            continue
        if value not in block.literal_agents:
            block.literal_agents.append(value)
    seen: set[str] = set()
    for m in SKILL_RE.finditer(segment):
        name = m.group(1)
        if name not in seen:
            seen.add(name)
            block.skills.append(name)
    return block


def parse_add_blocks(doc: str) -> list[AddBlock]:
    """Walk every ```bash block and extract its `add` command(s).

    A single fenced block may contain multiple independent `add` commands
    (delimited by shell `;` or by being on separate logical lines). Each
    such command becomes its own AddBlock so that flag validation and
    agent coverage checks run per command with NO cross-contamination
    of flags, agents, or skills between commands.
    """
    blocks: list[AddBlock] = []
    for idx, fence in enumerate(FENCED_BASH_RE.finditer(doc)):
        body = fence.group(1)
        if "npx" not in body or "skills@latest add" not in body:
            continue
        # Determine a fallback source for the block in case the first
        # segment is a `for ... do` opener (no `npx` of its own).
        first_match = ADD_CMD_RE.search(body)
        fallback_source = first_match.group("source") if first_match else ""
        for segment in _split_block_into_commands(body):
            ab = _extract_add_command(segment, fallback_source, idx)
            if ab is not None:
                blocks.append(ab)
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

    # --- Check 3: per-command flag/agent/skill checks, then union-level
    # agent and skill coverage per source. Each command is checked on its
    # own (no cross-contamination of flags, agents, skills), and then the
    # union of all commands for a source is verified to cover every
    # declared agent and every declared skill. ---
    for decl in decls:
        decl_skills = set(decl.skills)
        decl_agents = set(decl.agents)
        installed_skills: set[str] = set()
        union_agents: set[str] = set()
        for b in blocks_by_source.get(decl.name, []):
            # 3a. Required flags on every add command.
            if not b.has_global_flag:
                report(
                    errors,
                    f"install block #{b.block_index} for {decl.name!r} is "
                    f"missing the required --global flag on its `npx skills "
                    f"add` command",
                )
            if not b.has_copy_flag:
                report(
                    errors,
                    f"install block #{b.block_index} for {decl.name!r} is "
                    f"missing the required --copy flag on its `npx skills "
                    f"add` command",
                )
            # 3b. Per-command agent checks: literals must be in decl_agents;
            # loop usage must be consistent with decl_agents vs $AGENTS.
            if b.uses_agent_loop:
                if doc_agents:
                    extra = doc_agents - decl_agents
                    if extra:
                        report(
                            errors,
                            f"source {decl.name!r} install block iterates "
                            f"$AGENTS which includes {sorted(extra)}; these "
                            f"are not in the source's declared agents list "
                            f"({sorted(decl_agents)})",
                        )
                    missing_from_loop = decl_agents - doc_agents
                    if missing_from_loop:
                        report(
                            errors,
                            f"source {decl.name!r} declares agents "
                            f"{sorted(missing_from_loop)} but the doc's "
                            f"AGENTS set ({sorted(doc_agents)}) does not "
                            f"include them; the loop will not install on "
                            f"these agents",
                        )
                # The loop's reach contributes to the union.
                if doc_agents:
                    union_agents |= doc_agents
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
                union_agents |= set(b.literal_agents)
            # 3c. Skills added by this command must be declared.
            for skill in b.skills:
                if skill not in decl_skills:
                    report(
                        errors,
                        f"install block #{b.block_index} for {decl.name!r} "
                        f"installs --skill {skill!r} which is not declared in "
                        f"external-skills.yaml",
                    )
                installed_skills.add(skill)
        # 3d. Every declared skill for this source must be installed
        # (union across all commands for this source).
        missing_skills = decl_skills - installed_skills
        if missing_skills:
            report(
                errors,
                f"source {decl.name!r} declares skills {sorted(missing_skills)} "
                f"but no install block in docs/migration-npx.md adds them",
            )
        # 3e. Every declared agent for this source must appear in at
        # least one install command (union across all commands for this
        # source). This catches cases where the doc splits the install
        # across several commands (e.g. one for claude-code, one for
        # codex) and one of the declared agents has no command at all.
        if decl_agents:
            missing_agents = decl_agents - union_agents
            if missing_agents:
                report(
                    errors,
                    f"source {decl.name!r} declares agents "
                    f"{sorted(missing_agents)} but no install command in "
                    f"docs/migration-npx.md installs on them "
                    f"(union of literal_agents and $AGENTS reaches "
                    f"{sorted(union_agents)})",
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
        for s in decls_for_count
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
    # Build a set of character offsets that fall inside bash code blocks
    # containing an `add` command, so prose mentions of --force (even
    # right after a closed block) are not flagged.
    add_block_spans: list[tuple[int, int]] = []
    for m in FENCED_BASH_RE.finditer(doc):
        if "npx" in m.group(1) and "skills@latest add" in m.group(1):
            add_block_spans.append((m.start(), m.end()))
    for m in re.finditer(r"--force", doc):
        idx = m.start()
        in_add_block = any(start <= idx < end for start, end in add_block_spans)
        if in_add_block:
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
