# S1933/skills

Personal distribution of [Agent Skills](https://agentskills.net/) — installed
via [skills.sh](https://skills.sh/S1933/skills).

## Install

```bash
# All 11 skills, all agents, globally:
npx skills add S1933/skills --skill '*' --agent '*' --global -y

# Pick a single skill:
npx skills add S1933/skills --skill [REMOVED-INTERNAL-SKILL] --agent claude-code --global -y

# List what's in this repo first:
npx skills add S1933/skills --list
```

## Skills

| Skill | What it does |
|---|---|
| [`adapter-pattern`](adapter-pattern/) | Map one domain model to multiple external APIs, file formats, providers, CLIs, or versioned protocols without leaking vendor details into core logic. |
| [`atomic-file-write`](atomic-file-write/) | Replace configuration, state, generated, or user-owned files where partial writes, crashes, permissions, or concurrent readers can corrupt observable state. |
| [`binary-distribution`](binary-distribution/) | Release compiled CLI tools across OSes/architectures: version metadata, archives, checksums, signing, installers. |
| [`codex`](codex/) | Delegate to Codex CLI for an independent second opinion, verification, or deeper research. |
| [`embedded-fixtures`](embedded-fixtures/) | Ship deterministic templates, schemas, migrations, defaults, or sample files inside a Go binary via `embed`. |
| [`go-cli-conventions`](go-cli-conventions/) | Author, extend, or review Go 1.24+ CLI apps: Cobra commands, flags, exit behavior, config, testable boundaries. |
| [`golden-file-testing`](golden-file-testing/) | Test generated text, config, serialization, templates, compiler output where the full artifact shape matters. |
| [`repository-reconnaissance`](repository-reconnaissance/) | Build an evidence-based map of an unfamiliar repository before auditing, reviewing, or planning. |
| [`review-scope`](review-scope/) | Start a code review covering committed, staged, unstaged, and relevant untracked changes against the correct base. |
| [`[REMOVED-INTERNAL-SKILL]`]([REMOVED-INTERNAL-SKILL]/) | Integrate the Scaleflex / Filerobot / Cloudimage API: search DAM assets, upload, run Visual AI, invalidate CDN cache. |
| [`schema-validation`](schema-validation/) | Define or review validation for config files, API payloads, manifests, cross-field invariants, and human-readable errors. |

## Browse / discover more

This repo is intentionally minimal — only the skills I author and maintain here.
For everything else, search skills.sh:

```bash
npx skills find [query]
```

## Licence

[MIT](LICENSE) — Copyright (c) 2026 S1933.
