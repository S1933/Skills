#!/usr/bin/env python3
"""Validate external-skills.yaml against docs/migration-npx.md.

Checks: source↔block mapping, required flags (--global --copy --yes),
pair-based (agent,skill) coverage, --force prohibition, prose counts.
"""
from __future__ import annotations

import os
import re
import shlex
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MIGRATION_DOC = ROOT / "docs" / "migration-npx.md"
DEFAULT_EXTERNAL_YAML = ROOT / "external-skills.yaml"

FENCED_BASH_RE = re.compile(r"```bash\s*\n(.*?)\n```", re.DOTALL)
ADD_CMD_RE = re.compile(r"npx\s+--yes\s+skills@latest\s+add\s+(?P<source>[\w./-]+)")
LOOP_RE = re.compile(r"for\s+agent\s+in\s+\$AGENTS\b")

_REQUIRED_FLAGS = {"--global", "--copy"}


@dataclass
class Cmd:
    source: str
    agents: list[str] = field(default_factory=list)  # literal agents (no $agent)
    skills: list[str] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)  # e.g. {'--global','--copy','--yes'}
    loop: bool = False      # inside for agent in $AGENTS?
    uses_var: bool = False  # $agent appears in --agent values?
    block: int = 0

    @property
    def has(self) -> set[str]:
        return self.flags


@dataclass
class Decl:
    name: str
    skills: list[str]
    agents: list[str]
    claude_only: bool


# ── parsing ──────────────────────────────────────────────────────────

def parse_doc_agents(doc: str) -> set[str]:
    m = re.search(r'AGENTS\s*=\s*"([^"]+)"', doc)
    return set(m.group(1).split()) if m else set()


def _tokenize(text: str) -> list[str]:
    """shlex.split, with shell artifacts cleaned."""
    flat = re.sub(r"\\\s*\n", " ", text)
    try:
        tokens = shlex.split(flat)
    except ValueError:
        tokens = flat.split()
    # Strip trailing ; and \ from every token (they're shell syntax, not values).
    return [t.rstrip(";").rstrip("\\") for t in tokens]


_VALUE_FLAGS = {"--agent", "--skill"}


def _extract_flags(tokens: list[str]) -> dict[str, list[str]]:
    """Extract --flag values from token list. Only _VALUE_FLAGS collect values."""
    result: dict[str, list[str]] = {}
    current: str | None = None
    vals: list[str] = []
    for t in tokens:
        if t.startswith("--") and re.match(r"^--[\w][\w-]*$", t):
            if current and vals:
                result.setdefault(current, []).extend(vals)
            current = t
            vals = []
        elif current and current in _VALUE_FLAGS:
            v = t.strip('"').strip("'")
            if v:
                vals.append(v)
    if current and vals:
        result.setdefault(current, []).extend(vals)
    return result


def parse_cmds(doc: str) -> list[Cmd]:
    cmds: list[Cmd] = []
    for idx, m in enumerate(FENCED_BASH_RE.finditer(doc)):
        body = m.group(1)
        loop_body = bool(LOOP_RE.search(body))
        # A single fenced block may contain multiple `npx skills add` commands.
        for src_m in ADD_CMD_RE.finditer(body):
            source = src_m.group("source")
            # Extract the segment from this add command to the start of the
            # next one (or end of body). This scopes flag extraction to the
            # right command.
            next_m = ADD_CMD_RE.search(body, src_m.end())
            segment = body[src_m.start():next_m.start()] if next_m else body[src_m.start():]
            tokens = _tokenize(segment)
            flags = _extract_flags(tokens)

            agent_vals = flags.get("--agent", [])
            uses_var = any(v in {"$agent", "${agent}"} for v in agent_vals)
            literal_agents = [v for v in agent_vals if v not in {"$agent", "${agent}"}]
            skills = list(dict.fromkeys(flags.get("--skill", [])))

            present = {f for f in _REQUIRED_FLAGS if any(t == f for t in tokens)}
            after_sub = segment[src_m.end() - src_m.start():]
            if re.search(r"--yes\b", after_sub):
                present.add("--yes")

            cmds.append(Cmd(
                source=source, agents=literal_agents, skills=skills,
                flags=present, loop=loop_body, uses_var=uses_var, block=idx,
            ))
    return cmds


def load_decls(yaml_path: Path) -> list[Decl]:
    data = yaml.safe_load(yaml_path.read_text())
    decls: list[Decl] = []
    for key in ("sources", "maintained_locally"):
        for s in data.get(key, []):
            name = s.get("name") or s.get("source")
            if not name:
                continue
            decls.append(Decl(
                name=name,
                skills=list(s.get("selection", [])),
                agents=list(s.get("agents", [])),
                claude_only=bool(s.get("claude_code_only", False)),
            ))
    return decls


# ── validation ────────────────────────────────────────────────────────

def validate(migration: Path, external: Path) -> int:
    doc = migration.read_text()
    decls = load_decls(external)
    doc_agents = parse_doc_agents(doc)
    cmds = parse_cmds(doc)
    decl_by = {d.name: d for d in decls}
    by_source: dict[str, list[Cmd]] = defaultdict(list)
    for c in cmds:
        by_source[c.source].append(c)

    errors: list[str] = []
    err = lambda msg: (errors.append(msg), print(f"ERROR: {msg}"))

    # 1. Every declared source has ≥1 install block.
    for d in decls:
        if not by_source.get(d.name):
            err(f"source {d.name!r} declared in YAML has no add block in doc")

    # 2. Every install block maps to a declared source.
    for c in cmds:
        if c.source not in decl_by:
            err(f"block #{c.block} targets undeclared source {c.source!r}")

    # 3. Per-source pair-based coverage.
    for d in decls:
        d_skills = set(d.skills)
        d_agents = set(d.agents)
        covered: set[tuple[str, str]] = set()

        for c in by_source.get(d.name, []):
            missing = _REQUIRED_FLAGS - c.has
            for f in sorted(missing):
                err(f"block #{c.block} ({d.name}): missing required {f}")
            if "--yes" not in c.has:
                err(f"block #{c.block} ({d.name}): missing --yes on skills add")

            if c.uses_var and not c.loop:
                err(f"block #{c.block} ({d.name}): $agent in --agent but no for loop")

            # Effective agents.
            agents = set(c.agents)
            if c.loop and c.uses_var:
                agents |= doc_agents

            if not agents:
                err(f"block #{c.block} ({d.name}): no --agent and no $agent loop")

            for a in sorted(agents - d_agents):
                err(f"block #{c.block} ({d.name}): agent {a!r} not declared")
            for s in c.skills:
                if s not in d_skills:
                    err(f"block #{c.block} ({d.name}): skill {s!r} not declared")

            # Consistency: if using $agent in a loop, AGENTS should match.
            if c.loop and c.uses_var and doc_agents:
                extra = doc_agents - d_agents
                if extra:
                    err(f"{d.name}: loop AGENTS includes {sorted(extra)} not declared")
                missing_a = d_agents - doc_agents
                if missing_a:
                    err(f"{d.name}: declares {sorted(missing_a)} not in AGENTS set")

            for a in agents & d_agents:
                for s in c.skills:
                    if s in d_skills:
                        covered.add((a, s))

        # Pair coverage check (subsumes separate agent/skill checks).
        if d_agents and d_skills:
            expected = {(a, s) for a in d_agents for s in d_skills}
            missing = expected - covered
            if missing:
                by_agent: dict[str, list[str]] = defaultdict(list)
                for a, s in sorted(missing):
                    by_agent[a].append(s)
                for a, sk in sorted(by_agent.items()):
                    err(f"{d.name}: agent {a!r} missing skills {sorted(sk)}")

    # 4. Prose install counts.
    data = yaml.safe_load(external.read_text())
    all_entries = data.get("sources", []) + data.get("maintained_locally", [])
    total = sum(len(s.get("selection", [])) for s in all_entries)
    claude_only = sum(
        len(s.get("selection", [])) for s in all_entries if s.get("claude_code_only")
    )
    exp_claude = total
    exp_other = total - claude_only

    pm = re.search(
        r"(\d+)\s+skills?\s+installed\s+for\s+`?claude-code`?\s*;\s*"
        r"(\d+)\s+for\s+`?codex`?",
        doc, re.IGNORECASE,
    )
    if not pm:
        err(f"doc should state per-agent counts (e.g. {exp_claude} for claude-code; "
            f"{exp_other} for codex)")
    else:
        doc_cl, doc_ot = int(pm.group(1)), int(pm.group(2))
        if doc_cl != exp_claude:
            err(f"doc says {doc_cl} claude-code skills, YAML implies {exp_claude}")
        if doc_ot != exp_other:
            err(f"doc says {doc_ot} other-agent skills, YAML implies {exp_other}")

    # 5. --force in any add block.
    add_spans = [
        (m.start(), m.end()) for m in FENCED_BASH_RE.finditer(doc)
        if "skills@latest add" in m.group(1)
    ]
    for m in re.finditer(r"--force", doc):
        if any(start <= m.start() < end for start, end in add_spans):
            err(f"--force in add block at offset {m.start()} (use --yes)")

    if errors:
        print(f"\n{len(errors)} error(s)")
        return 1
    print(f"OK — {len(cmds)} block(s), {len(decls)} source(s)")
    return 0


def resolve_paths(argv: list[str] | None = None) -> tuple[Path, Path]:
    if argv is None:
        argv = sys.argv[1:]
    mig = (Path(argv[0]).expanduser() if len(argv) >= 1 and argv[0]
           else Path(os.environ.get("EXTERNAL_SKILLS_MIGRATION_DOC", ""))
           if os.environ.get("EXTERNAL_SKILLS_MIGRATION_DOC")
           else DEFAULT_MIGRATION_DOC)
    ext = (Path(argv[1]).expanduser() if len(argv) >= 2 and argv[1]
           else Path(os.environ.get("EXTERNAL_SKILLS_YAML", ""))
           if os.environ.get("EXTERNAL_SKILLS_YAML")
           else DEFAULT_EXTERNAL_YAML)
    return mig, ext


if __name__ == "__main__":
    mig_path, ext_path = resolve_paths()
    raise SystemExit(validate(mig_path, ext_path))
