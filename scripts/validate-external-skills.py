#!/usr/bin/env python3
"""Validate external-skills.yaml consistency with docs/migration-npx.md.

Strengthened per review:
- Parses every ```bash code block that runs an `npx ... skills@latest add`
  command, rather than substring-searching the whole Markdown file.
- Verifies source / agent / skill mappings structurally against
  external-skills.yaml (declarations ↔ install blocks).
- Scans every --force occurrence, not just the first.
- Per-command parsing: each `npx skills@latest add` invocation in a fenced
  block becomes its own AddBlock with its own flags/agents/skills; flags
  and selections never bleed across commands.
- Pair-based agent+skill coverage: instead of checking agent and skill
  unions independently (which accepted configurations where agent A only
  got skill X and agent B only got skill Y), the validator builds the
  Cartesian product of agents and skills per command and verifies that
  every declared (agent, skill) pair is covered.
- Variadic option parsing: --agent and --skill accept multiple values
  (e.g. `--agent claude-code codex`), matching the real CLI behaviour.
- --yes flag verification: the validator checks that the `skills add`
  --yes confirmation flag is present (separate from npx's --yes).

The doc may reference removed/legacy skills in prose or in `remove` blocks
without invalidating the validator.

The migration doc and external-skills.yaml paths can be overridden for
testing (and for ad-hoc runs against fixtures) via:

  - CLI args:  python validate-external-skills.py [migration_doc] [external_yaml]
  - env vars:  EXTERNAL_SKILLS_MIGRATION_DOC, EXTERNAL_SKILLS_YAML

If neither is supplied, the script falls back to the canonical
`<repo>/docs/migration-npx.md` and `<repo>/external-skills.yaml` paths.
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIGRATION_DOC = ROOT / "docs" / "migration-npx.md"
DEFAULT_EXTERNAL_YAML = ROOT / "external-skills.yaml"

# Match a fenced ```bash ... ``` block. The regex is non-greedy and allows
# the closing fence to be anywhere on its own line.
FENCED_BASH_RE = re.compile(
    r"```bash\s*\n(.*?)\n```",
    re.DOTALL,
)

# Match an `npx ... skills@latest add <source> ...` command line. We pull
# out the source repo and the position of the subcommand's end (for
# detecting the `skills add` --yes flag after the subcommand).
ADD_CMD_RE = re.compile(
    r"npx\s+--yes\s+skills@latest\s+add\s+(?P<source>[\w./-]+)"
)

ADD_CMD_HEAD_RE = re.compile(r"npx\s+--yes\s+skills@latest\s+add\b")
GLOBAL_FLAG_RE = re.compile(r"(?:^|\s)--global(?:\s|$)")
COPY_FLAG_RE = re.compile(r"(?:^|\s)--copy(?:\s|$)")
# Match --yes that appears AFTER the subcommand (not npx's --yes).
# Used with a substring from the end of the add subcommand.
YES_FLAG_RE = re.compile(r"--yes\b")


# Flags known to accept variadic values. Boolean flags (--yes, --global,
# --copy, --force) are detected by dedicated regexes; the variadic parser
# only accumulates values for flags in this set.
_VARIADIC_VALUE_FLAGS = {"agent", "skill"}


def _parse_variadic_options(segment: str) -> dict[str, list[str]]:
    """Parse variadic --flag options from a command segment.

    Tokenises on whitespace and walks the token stream. When a token is a
    --flag, all following non-flag tokens are collected as its values
    until the next --flag or end of stream — but ONLY for flags listed
    in _VARIADIC_VALUE_FLAGS. Boolean flags (--yes, --global, --copy,
    etc.) are recognised but do not consume following tokens as values.
    Shell variables (tokens starting with $) are skipped.

    Returns {flag_name: [values...]} for every --flag that has values.
    """
    tokens = segment.split()
    result: dict[str, list[str]] = {}
    current_flag: str | None = None
    current_values: list[str] = []

    for token in tokens:
        m = re.match(r"^--([\w][\w-]*)$", token)
        if m:
            # Save previous flag's accumulated values.
            if current_flag is not None and current_values:
                result.setdefault(current_flag, []).extend(current_values)
            current_flag = m.group(1)
            current_values = []
            continue

        # Not a flag — it's a value only if the current flag accepts values.
        if current_flag is not None and current_flag in _VARIADIC_VALUE_FLAGS:
            # Skip shell variables like $AGENTS or "$agent".
            if token.startswith("$"):
                continue
            # Clean up trailing ; or \ (shell separators / continuations).
            token = token.rstrip(";").rstrip("\\")
            # Remove shell quotes.
            token = token.strip('"').strip("'")
            if token:
                current_values.append(token)

    # Don't forget the last flag.
    if current_flag is not None and current_values:
        result.setdefault(current_flag, []).extend(current_values)

    return result


@dataclass
class AddBlock:
    """A single `npx skills@latest add` command (one per command, not per
    fenced block)."""

    source: str
    # Agents targeted by this command. Derived from --agent flag(s).
    literal_agents: list[str] = field(default_factory=list)
    # Skills installed by this command. Derived from --skill flag(s).
    skills: list[str] = field(default_factory=list)
    # True if the command uses `for agent in $AGENTS` (or similar loop).
    # When true, the per-command agent reach is the AGENTS set defined at
    # the top of the doc.
    uses_agent_loop: bool = False
    # True if this command carries the required --global flag.
    has_global_flag: bool = False
    # True if this command carries the required --copy flag.
    has_copy_flag: bool = False
    # True if this command carries the `skills add` --yes confirmation
    # flag (the one AFTER the subcommand, not npx's own --yes).
    has_yes_flag: bool = False
    # Index of the parent fenced block, for error reporting.
    block_index: int = 0


@dataclass
class SourceDecl:
    """A source entry from external-skills.yaml."""

    name: str
    skills: list[str]
    agents: list[str]
    claude_code_only: bool


def load_source_decls(external_yaml: Path = DEFAULT_EXTERNAL_YAML) -> list[SourceDecl]:
    """Read the sources + maintained_locally entries from external-skills.yaml.

    Both sections describe installable selections. `sources` use a `name:`
    key; `maintained_locally` entries use `source:`. From the validator's
    perspective, both must have install blocks in the doc.
    """
    data = yaml.safe_load(Path(external_yaml).read_text())
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
      5. Track `in_agent_loop` state across commands: once a
         `for agent in $AGENTS; do` is seen, every subsequent add command
         in the same fenced block inherits the `uses_agent_loop=True`
         marker until a `done` closes the loop. Without this rule, a
         loop containing two `npx skills@latest add` commands would
         correctly attach the marker to the first command but miss the
         second, and the validator would reject a valid shell
         configuration.
    """
    # Normalize line continuations: " \<newline>" -> " " so the block
    # reads as a single logical line per `;` segment.
    flat = re.sub(r"\\\s*\n", " ", body)
    # Split on shell `;` to get individual commands.
    semicolon_segments = [seg.strip() for seg in flat.split(";") if seg.strip()]

    # Within each `;` segment, split on a fresh `npx ... skills@latest add`.
    raw_parts: list[str] = []
    for seg in semicolon_segments:
        cursor = 0
        for m in re.finditer(ADD_CMD_HEAD_RE, seg):
            if m.start() > cursor:
                head = seg[cursor : m.start()].strip()
                if head:
                    raw_parts.append(head)
            end = m.end()
            nxt = ADD_CMD_HEAD_RE.search(seg, end)
            stop = nxt.start() if nxt else len(seg)
            raw_parts.append(seg[m.start() : stop].strip())
            cursor = stop
        if cursor < len(seg):
            tail = seg[cursor:].strip()
            if tail:
                raw_parts.append(tail)

    # Fold `for ... do` preambles into the next add command so the
    # per-command loop marker is preserved. Once a `for ... do` has
    # been seen, the loop state persists across ALL subsequent add
    # commands in the same block until a `done` closes it.
    commands: list[str] = []
    pending_preamble: list[str] = []
    in_agent_loop = False
    for part in raw_parts:
        if ADD_CMD_HEAD_RE.search(part):
            preamble = list(pending_preamble)
            if in_agent_loop and not any(
                re.search(r"for\s+agent\s+in\s+\$AGENTS", p) for p in preamble
            ):
                preamble.append("for agent in $AGENTS; do")
            merged = " ".join(preamble + [part])
            commands.append(merged)
            pending_preamble = []
        elif re.search(r"\bdone\b", part):
            in_agent_loop = False
            pending_preamble = []
            continue
        elif _is_for_loop_opener(part):
            pending_preamble.append(part)
            in_agent_loop = True
        else:
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

    # Check for `skills add` --yes AFTER the subcommand (not npx's --yes).
    add_end = cmd_match.end()
    block.has_yes_flag = bool(YES_FLAG_RE.search(segment[add_end:]))

    # Variadic option parsing: --agent and --skill accept multiple values.
    opts = _parse_variadic_options(segment)
    block.literal_agents = [a for a in opts.get("agent", []) if not a.startswith("$")]
    # Deduplicate while preserving order.
    seen_agents: set[str] = set()
    deduped_agents: list[str] = []
    for a in block.literal_agents:
        if a not in seen_agents:
            seen_agents.add(a)
            deduped_agents.append(a)
    block.literal_agents = deduped_agents

    seen_skills: set[str] = set()
    deduped_skills: list[str] = []
    for s in opts.get("skill", []):
        if s not in seen_skills:
            seen_skills.add(s)
            deduped_skills.append(s)
    block.skills = deduped_skills

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


def resolve_paths(argv: list[str] | None = None) -> tuple[Path, Path]:
    """Resolve migration-doc and external-yaml paths from CLI args / env / defaults.

    Precedence (highest first):
      1. CLI positional args: argv[0] = migration_doc, argv[1] = external_yaml.
      2. Environment variables: EXTERNAL_SKILLS_MIGRATION_DOC,
         EXTERNAL_SKILLS_YAML.
      3. Hardcoded defaults relative to the script's ROOT.
    """
    if argv is None:
        argv = sys.argv[1:]
    migration = (
        Path(argv[0]).expanduser()
        if len(argv) >= 1 and argv[0]
        else Path(os.environ["EXTERNAL_SKILLS_MIGRATION_DOC"]).expanduser()
        if os.environ.get("EXTERNAL_SKILLS_MIGRATION_DOC")
        else DEFAULT_MIGRATION_DOC
    )
    external = (
        Path(argv[1]).expanduser()
        if len(argv) >= 2 and argv[1]
        else Path(os.environ["EXTERNAL_SKILLS_YAML"]).expanduser()
        if os.environ.get("EXTERNAL_SKILLS_YAML")
        else DEFAULT_EXTERNAL_YAML
    )
    return migration, external


def main(
    migration_doc: Path | None = None,
    external_yaml: Path | None = None,
) -> int:
    if migration_doc is None or external_yaml is None:
        cli_doc, cli_yaml = resolve_paths()
        if migration_doc is None:
            migration_doc = cli_doc
        if external_yaml is None:
            external_yaml = cli_yaml
    migration_doc = Path(migration_doc)
    external_yaml = Path(external_yaml)

    doc = migration_doc.read_text()
    decls = load_source_decls(external_yaml)
    doc_agents = parse_doc_agent_set(doc)
    add_blocks = parse_add_blocks(doc)

    # Index declarations by source name.
    decl_by_name: dict[str, SourceDecl] = {d.name: d for d in decls}

    # Group install blocks by source so we can pair-check.
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

    # --- Check 3: per-command flag/agent/skill checks, then PAIR-BASED
    # agent × skill coverage per source. Each command is checked on its
    # own (no cross-contamination of flags, agents, skills), and then
    # the union of all commands for a source is verified to cover every
    # declared (agent, skill) pair — not just the independent unions.
    # ---
    for decl in decls:
        decl_skills = set(decl.skills)
        decl_agents = set(decl.agents)
        # Pairs actually covered by install commands: {(agent, skill), ...}
        covered_pairs: set[tuple[str, str]] = set()
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
            if not b.has_yes_flag:
                report(
                    errors,
                    f"install block #{b.block_index} for {decl.name!r} is "
                    f"missing the required --yes confirmation flag on its "
                    f"`skills add` command (the --yes after the subcommand, "
                    f"not npx's --yes)",
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
                # The loop's reach: every agent in $AGENTS gets every skill
                # this command installs.
                cmd_agents = doc_agents if doc_agents else set()
                union_agents |= cmd_agents
                for agent in cmd_agents:
                    for skill in b.skills:
                        if agent in decl_agents and skill in decl_skills:
                            covered_pairs.add((agent, skill))
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
                for agent in b.literal_agents:
                    if agent in decl_agents:
                        for skill in b.skills:
                            if skill in decl_skills:
                                covered_pairs.add((agent, skill))

            # 3c. Skills added by this command must be declared.
            for skill in b.skills:
                if skill not in decl_skills:
                    report(
                        errors,
                        f"install block #{b.block_index} for {decl.name!r} "
                        f"installs --skill {skill!r} which is not declared in "
                        f"external-skills.yaml",
                    )

        # 3d. Every declared (agent, skill) pair must be covered.
        if decl_agents and decl_skills:
            expected_pairs = {(a, s) for a in decl_agents for s in decl_skills}
            missing_pairs = expected_pairs - covered_pairs
            if missing_pairs:
                # Group by agent for readable error messages.
                by_agent: dict[str, list[str]] = defaultdict(list)
                for agent, skill in sorted(missing_pairs):
                    by_agent[agent].append(skill)
                for agent, skills in sorted(by_agent.items()):
                    report(
                        errors,
                        f"source {decl.name!r}: agent {agent!r} is missing "
                        f"install coverage for skills {sorted(skills)} "
                        f"(the (agent, skill) pair is not covered by any "
                        f"install command)",
                    )

        # 3e. Every declared skill must be installed at least once
        # (quick check: if a skill has zero covered pairs, it's missing).
        installed_skills = {s for _, s in covered_pairs}
        missing_skills = decl_skills - installed_skills
        if missing_skills:
            report(
                errors,
                f"source {decl.name!r} declares skills {sorted(missing_skills)} "
                f"but no install block in docs/migration-npx.md adds them",
            )

        # 3f. Every declared agent must appear in at least one install
        # command (union across all commands for this source).
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
    data = yaml.safe_load(external_yaml.read_text())
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
