# S1933 skills registry

A declarative registry of [agent skills](https://skills.sh/) installed via `npx skills add`. No skill content is versioned here — only the manifest pointing at upstream sources.

## Hybrid strategy

A `mattpocock/skills` × `obra/superpowers` hybrid, based on a comparative analysis:

- **Matt Pocock** = engineering discipline (grilling, TDD, diagnosing, codebase-design, domain-modeling)
- **Superpowers** = execution/orchestration (worktrees, subagents, parallel dispatch, verification, finishing branch)

We don't install both collections in full to avoid rule collisions and duplicates.

## Install

```bash
# Install all 27 verified skills
./install.sh

# Preview without executing
./install.sh --dry-run

# Install one skill
./install.sh --only tdd
```

`install.sh` wraps `npx skills add <repo-url> --skill <name>` for every entry in [`registry.json`](./registry.json).

## Registry

[`registry.json`](./registry.json) — flat list of 27 entries:

```json
{
  "name": "tdd",
  "owner": "mattpocock",
  "repo": "skills",
  "role": "implementation"
}
```

Each entry has a `role` documenting why it's in the registry: `discovery`, `design`, `implementation`, `quality`, `delivery`, or `style`.

Run `./validate-registry.sh` to assert `count === skills.length`, no duplicates, and valid roles. CI runs the same check on every push (`.github/workflows/validate-registry.yml`).

## Sources

| Source | Count | Role |
|---|---:|---|
| `mattpocock/skills` | 15 | Engineering discipline |
| `obra/superpowers` | 9 | Execution / orchestration |
| `juliusbrussee/caveman` | 1 | Output style |
| `ayghri/i-have-adhd` | 1 | Output style |
| `ksimback/tech-debt-skill` | 1 | Audit |

## Adding a skill

1. Confirm upstream exists on [skills.sh](https://skills.sh/).
2. Edit `registry.json` — add `{ "name", "owner", "repo", "role" }`. `role` ∈ `discovery`, `design`, `implementation`, `quality`, `delivery`, `style`.
3. Run `./install.sh --dry-run --only=<name>` to verify the command.
4. Run `./validate-registry.sh` to confirm integrity.
5. Commit and push — CI runs both checks.

## Why a manifest, not a fork

Versioning the `SKILL.md` content forced constant re-syncs with upstream. The manifest is a single source of truth for **what to install**, while skills.sh stays the source of truth for **the content itself**. To upgrade: re-run `./install.sh` after upstream bumps.

## Layout

```
.
├── README.md
├── registry.json           # 27 skills, declarative
└── install.sh              # one-shot installer
```

The repo ships zero skill content. Run `./install.sh` to pull everything from skills.sh.
