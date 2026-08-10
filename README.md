# S1933 skills registry

A declarative registry of [agent skills](https://skills.sh/) installed via `npx skills add`. No skill content is versioned here — only the manifest pointing at upstream sources.

## Install

```bash
# Install all 23 verified skills
./install.sh

# Preview without executing
./install.sh --dry-run

# Install one skill
./install.sh --only tdd
```

`install.sh` wraps `npx skills add <repo-url> --skill <name>` for every entry in [`registry.json`](./registry.json).

## Registry

[`registry.json`](./registry.json) — flat list of 23 entries:

```json
{
  "name": "tdd",
  "owner": "mattpocock",
  "repo": "skills"
}
```

Entries with `"source": "tbd"` are skipped by default. Pass `--all` to attempt them anyway.

## Sources

| Source | Count | Skills |
|---|---|---|
| `mattpocock/skills` | 20 | code-review, codebase-design, diagnosing-bugs, dispatching-parallel-agents, domain-modeling, finishing-a-development-branch, grill-with-docs, grilling, handoff, improve-codebase-architecture, receiving-code-review, requesting-code-review, setup-matt-pocock-skills, tdd, to-spec, to-tickets, triage, verification-before-completion, wait-what, writing-for-agents |
| `juliusbrussee/caveman` | 1 | caveman |
| `ayghri/i-have-adhd` | 1 | i-have-adhd |
| `ksimback/tech-debt-skill` | 1 | tech-debt-audit |

## Adding a skill

1. Confirm upstream exists on [skills.sh](https://skills.sh/).
2. Edit `registry.json` — add `{ "name", "owner", "repo" }`.
3. Run `./install.sh --dry-run --only=<name>` to verify the command.
4. Commit and push.

## Why a manifest, not a fork

Versioning the `SKILL.md` content forced constant re-syncs with upstream. The manifest is a single source of truth for **what to install**, while skills.sh stays the source of truth for **the content itself**. To upgrade: re-run `./install.sh` after upstream bumps.

## Layout

```
.
├── README.md
├── registry.json           # 23 skills, declarative
└── install.sh              # one-shot installer
```

The repo ships zero skill content. Run `./install.sh` to pull everything from skills.sh.
