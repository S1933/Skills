# S1933 skills registry

A declarative manifest of agent skills. No skill content is versioned — only `{name, owner, repo, role}` entries. Run `./install.sh` to pull everything from [skills.sh](https://skills.sh/).

## Install

```bash
./install.sh                  # install all 27 skills
./install.sh --dry-run        # preview
./install.sh --only tdd       # install one
./validate-registry.sh        # assert count === skills.length, valid roles
```

## Hybrid

Matt Pocock (engineering discipline) × obra/superpowers (execution/orchestration). Both collections in full would create rule collisions and duplicates, so we picked the best of each.

| Source | Count | Role |
|---|---:|---|
| `mattpocock/skills` | 15 | Engineering (grilling, TDD, diagnosing, code review, codebase-design) |
| `obra/superpowers` | 8 | Execution (worktrees, subagents, dispatch, verification, finishing) |
| `multica-ai/andrej-karpathy-skills` | 1 | Coding discipline (anti-overengineering) |
| `anthropics/knowledge-work-plugins` | 1 | Tech debt audit |
| `juliusbrussee/caveman` | 1 | Output style |
| `ayghri/i-have-adhd` | 1 | Output style |

## Registry

`registry.json` is a flat list. Each entry has a `role` ∈ `discovery`, `design`, `implementation`, `setup`, `quality`, `delivery`, `style` documenting why it's here.

```json
{"name": "tdd", "owner": "mattpocock", "repo": "skills", "role": "implementation"}
```

Skills with a HARD-GATE upstream (e.g. `obra/superpowers/brainstorming`) are excluded — they conflict with the hybrid.

## Add a skill

1. Confirm upstream on [skills.sh](https://skills.sh/).
2. Edit `registry.json` — add `{name, owner, repo, role}`.
3. `./install.sh --dry-run --only=<name>` then `./validate-registry.sh`.
4. Push — CI re-runs both checks. `verify-upstreams.yml` runs weekly.

## Layout

```
.
├── README.md
├── registry.json          # 27 entries
├── install.sh
├── validate-registry.sh
└── .github/workflows/     # CI on push/PR + weekly upstream check
```
