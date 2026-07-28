# Initial skill validation audit

Audit date: 2026-07-28

Scope: all files tracked on `main` before the catalogue improvement programme,
plus the Codex safety regression added as the programme's first task.

## Catalogue inventory

- Tracked skills: 51
- Skill directories missing `SKILL.md`: 0
- YAML frontmatter parse failures: 0
- Missing `name` or `description`: 0
- Directory/name mismatches: 0
- Duplicate skill names: 0
- Broken relative Markdown links: 0

Every tracked skill is represented in `skills-manifest.yaml`.

## Supporting code

- Bash syntax: passed for four tracked `.sh` scripts.
- Zsh syntax: passed for `[REMOVED-INTERNAL-SKILL]/rr.zsh`.
- ShellCheck: passed for the four Bash scripts.
- JSON fenced examples: 5 checked, 0 parse failures.
- YAML fenced examples: 93 checked, 8 do not parse as standalone YAML.
- Graphviz fenced examples: 10 found; compilation skipped because `dot` is
  not installed.

The eight YAML failures are [REMOVED-INTERNAL-SKILL] excerpts containing template expressions,
partial lists, or multiple adjacent fragments. They occur in:

- `[REMOVED-INTERNAL-SKILL]/SKILL.md` (1 block)
- `[REMOVED-INTERNAL-SKILL]/references/actions-models-templates.md` (1 block)
- `[REMOVED-INTERNAL-SKILL]/references/conventions.md` (2 blocks)
- `[REMOVED-INTERNAL-SKILL]/references/core-syntax.md` (3 blocks)
- `[REMOVED-INTERNAL-SKILL]/references/workflow-patterns.md` (1 block)

These require explicit validator exceptions or conversion into complete
standalone examples.

## Discovery and dependency findings

- At baseline, `implement` referred to undeclared `tdd` and `review` command aliases; Phase 4 replaced them with canonical skill names.
- Review skill descriptions contain slash-command comparisons instead of only
  observable trigger conditions.
- Several automatic descriptions do not start with `Use when`.
- Cross-skill dependencies are described in prose and are not machine-readable.
- Client/tool/runtime compatibility is not consistently declared.

## Safety and portability findings

- The original Codex guidance used approval and sandbox bypass in every command
  example. The new regression suite captured six failures before the safety
  guidance was changed.
- The Git guardrail hook uses substring matching, depends on `jq`, and allows
  execution when input extraction fails.
- `[REMOVED-INTERNAL-SKILL]` and `[REMOVED-INTERNAL-SKILL]` contain personal paths or environment assumptions.
- [REMOVED-INTERNAL-SKILL] reference examples contain internal hostnames.
- `[REMOVED-INTERNAL-SKILL]` contains local paths and machine-specific network
  workarounds.

## Context-size findings

The largest main skill files at baseline are:

| Skill | Approximate words |
|---|---:|
| writing-skills | 3,807 |
| subagent-driven-development | 3,083 |
| improve | 2,310 |
| tech-debt-audit | 1,951 |
| [REMOVED-INTERNAL-SKILL] | 1,931 |
| brainstorming | 1,553 |
| systematic-debugging | 1,504 |
| test-driven-development | 1,496 |
| using-git-worktrees | 1,154 |
| codex | 1,096 |

Size limits should begin as warnings so progressive-disclosure refactors can
land before limits become merge-blocking.
