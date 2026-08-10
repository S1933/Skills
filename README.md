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

Each entry has a `role` documenting why it's in the registry: `discovery`, `design`, `implementation`, `setup`, `quality`, `delivery`, or `style`.

Run `./validate-registry.sh` to assert `count === skills.length`, no duplicates, and valid roles. CI runs the same check on every push (`.github/workflows/validate-registry.yml`).

## Sources

| Source | Count | Role |
|---|---:|---|
| `mattpocock/skills` | 15 | Engineering discipline |
| `obra/superpowers` | 8 | Execution / orchestration |
| `multica-ai/andrej-karpathy-skills` | 1 | Coding discipline (anti-overengineering) |
| `juliusbrussee/caveman` | 1 | Output style |
| `ayghri/i-have-adhd` | 1 | Output style |
| `ksimback/tech-debt-skill` | 1 | Audit |

## Adding a skill

1. Confirm upstream exists on [skills.sh](https://skills.sh/).
2. Check there is no equivalent already in the registry (Matt vs Superpowers overlap check).
3. Edit `registry.json` — add `{ "name", "owner", "repo", "role" }`. `role` ∈ `discovery`, `design`, `implementation`, `setup`, `quality`, `delivery`, `style`.
4. Run `./install.sh --dry-run --only=<name>` to verify the command.
5. Run `./validate-registry.sh` to confirm integrity.
6. Commit and push — CI runs both checks.

Skills with a HARD-GATE upstream (e.g. `obra/superpowers/brainstorming`) are not eligible for the hybrid: they conflict with the Matt-driven engineering flow.

## Why a manifest, not a fork

Versioning the `SKILL.md` content forced constant re-syncs with upstream. The manifest is a single source of truth for **what to install**, while skills.sh stays the source of truth for **the content itself**. To upgrade: re-run `./install.sh` after upstream bumps.

## Layout

```
.
├── README.md
├── registry.json                       # 27 skills, declarative
├── install.sh                          # one-shot installer
├── validate-registry.sh                # integrity guard
└── .github/
    └── workflows/
        └── validate-registry.yml       # CI on push/PR
```

The repo ships zero skill content. Run `./install.sh` to pull everything from skills.sh.
