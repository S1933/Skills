# S1933 skills registry

A declarative manifest of agent skills. No skill content is versioned here — only `{name, owner, repo, role}` entries in `registry.json`. Skill files are pulled at install time from upstream repositories on [skills.sh](https://skills.sh/).

## Quick start

```bash
./install.sh            # wipe local skills (gitignore-respecting) + install everything
./install.sh --dry-run  # preview without touching anything
./validate-registry.sh  # assert count === skills.length, valid roles, no duplicates
```

`./install.sh` is idempotent: every run wipes the previous install (respecting `.gitignore`) and reinstalls the full registry from scratch. There are no other flags by design — keep the surface small.

### Why installs are global

This checkout **is** the global skills directory: `~/.claude/skills` is a symlink to `~/.agents/skills`, which is this repo. So `install.sh` runs `npx skills add -g`, whose global root is exactly `~/.agents/skills` — the repo root. Skills land as top-level directories next to `registry.json`.

Without `-g` the CLI detects a project (this repo has a `.git`) and nests everything under `./.agents/skills/` with symlinks in `./.claude/skills/`, producing a `~/.agents/skills/.agents/skills/` doubling. `install.sh` deletes those paths on every run, and `.gitignore` blocks them.

## What's in here

| Source | Count | Role |
|---|---:|---|
| [`mattpocock/skills`](https://github.com/mattpocock/skills) | 16 | Engineering (grilling, TDD, diagnosing, code review, codebase-design) |
| [`obra/superpowers`](https://github.com/obra/superpowers) | 8 | Execution (worktrees, subagents, dispatch, verification, finishing) |
| [`multica-ai/andrej-karpathy-skills`](https://github.com/multica-ai/andrej-karpathy-skills) | 1 | Coding discipline (anti-overengineering) |
| [`anthropics/knowledge-work-plugins`](https://github.com/anthropics/knowledge-work-plugins) | 1 | Tech debt audit |
| [`juliusbrussee/caveman`](https://github.com/juliusbrussee/caveman) | 1 | Output style |
| [`ayghri/i-have-adhd`](https://github.com/ayghri/i-have-adhd) | 1 | Output style |
| [`humanlayer/skills`](https://github.com/humanlayer/skills) | 1 | Visual explanation (`show-me`) |
| [`hardikpandya/stop-slop`](https://github.com/hardikpandya/stop-slop) | 1 | Prose de-slop (remove AI tells) |
| [`getsentry/skills`](https://github.com/getsentry/skills) | 1 | Security review (OWASP-based) |
| **Total** | **31** | |

Matt Pocock (engineering discipline) × obra/superpowers (execution/orchestration). Both collections in full would create rule collisions and duplicates, so we picked the best of each. `obra/superpowers/brainstorming` is excluded — its HARD-GATE clashes with the hybrid.

## Roles

Each `registry.json` entry has a `role` ∈ {`discovery`, `design`, `implementation`, `setup`, `quality`, `delivery`, `style`} documenting why it's here. Current distribution:

| Role | Count | What it covers |
|---|---:|---|
| `discovery` | 3 | `grilling`, `grill-with-docs`, `wait-what` — sharpen the question before designing |
| `design` | 7 | `codebase-design`, `domain-modeling`, `prototype`, `to-spec`, `to-tickets`, `improve-codebase-architecture`, `writing-for-agents` |
| `implementation` | 5 | `tdd`, `dispatching-parallel-agents`, `executing-plans`, `subagent-driven-development`, `using-git-worktrees` |
| `quality` | 8 | `code-review`, `diagnosing-bugs`, `karpathy-guidelines`, `receiving-code-review`, `requesting-code-review`, `security-review`, `tech-debt`, `triage` |
| `delivery` | 3 | `finishing-a-development-branch`, `handoff`, `verification-before-completion` |
| `style` | 4 | `caveman`, `i-have-adhd`, `show-me`, `stop-slop` — output shape |
| `setup` | 1 | `setup-matt-pocock-skills` — onboarding |

## Full skill list

| Skill | Source | Role | What it does |
|---|---|---:|---|
| `caveman` | juliusbrussee/caveman | style | Ultra-compressed output mode |
| `code-review` | mattpocock/skills | quality | Review changes since a fixed point (commit/branch) |
| `codebase-design` | mattpocock/skills | design | Shared vocabulary for designing deep modules |
| `diagnosing-bugs` | mattpocock/skills | quality | Rigorous diagnosis loop for hard bugs/regressions |
| `dispatching-parallel-agents` | obra/superpowers | implementation | Run independent tasks across parallel agents |
| `domain-modeling` | mattpocock/skills | design | Build and sharpen a project's domain model |
| `executing-plans` | obra/superpowers | implementation | Execute a written implementation plan |
| `finishing-a-development-branch` | obra/superpowers | delivery | Wrap up a completed branch (verify, merge) |
| `grill-with-docs` | mattpocock/skills | discovery | Sharpen a plan via docs-grounded interrogation |
| `grilling` | mattpocock/skills | discovery | Interview the user relentlessly about a plan |
| `handoff` | mattpocock/skills | delivery | Compact a conversation into a handoff document |
| `i-have-adhd` | ayghri/i-have-adhd | style | Shape output for a reader with ADHD |
| `improve-codebase-architecture` | mattpocock/skills | design | Scan for deepening opportunities in a codebase |
| `karpathy-guidelines` | multica-ai/andrej-karpathy-skills | quality | Reduce common LLM coding mistakes |
| `prototype` | mattpocock/skills | design | Throwaway prototype to answer a design question |
| `receiving-code-review` | obra/superpowers | quality | Handle inbound review feedback correctly |
| `requesting-code-review` | obra/superpowers | quality | Pre-commit review (security, quality gates) |
| `security-review` | getsentry/skills | quality | Security code review for vulnerabilities (OWASP-based) |
| `setup-matt-pocock-skills` | mattpocock/skills | setup | Configure this repo for the engineering skills |
| `show-me` | humanlayer/skills | style | Explain the current topic visually |
| `stop-slop` | hardikpandya/stop-slop | style | Remove AI writing patterns from prose |
| `subagent-driven-development` | obra/superpowers | implementation | Execute plans via delegated subagents |
| `tdd` | mattpocock/skills | implementation | Test-driven development (RED-GREEN-REFACTOR) |
| `tech-debt` | anthropics/knowledge-work-plugins | quality | Identify, categorize, prioritize technical debt |
| `to-spec` | mattpocock/skills | design | Turn a conversation into a spec |
| `to-tickets` | mattpocock/skills | design | Break a plan/spec into tickets |
| `triage` | mattpocock/skills | quality | Move issues through a state machine of roles |
| `using-git-worktrees` | obra/superpowers | implementation | Isolated feature work via git worktrees |
| `verification-before-completion` | obra/superpowers | delivery | Verify before claiming work is done |
| `wait-what` | mattpocock/skills | discovery | Re-pitch when a message didn't land |
| `writing-for-agents` | mattpocock/skills | design | Write documents for agents to consume |

## Registry format

```json
{"name": "tdd", "owner": "mattpocock", "repo": "skills", "role": "implementation"}
```

- `name` — unique across the registry (namespace collision guard)
- `owner` + `repo` — source identity, must match upstream
- `role` — required, one of the seven above
- `count` at the top must equal `skills.length` (asserted by `validate-registry.sh`)

The lockfile lives outside this repo. Global installs record their state in `~/.agents/.skill-lock.json`, shared with skills installed by other means (the private ones below), so `./install.sh` never rewrites it wholesale — `npx skills add` updates its own entries.

## Add a skill

1. Confirm upstream on [skills.sh](https://skills.sh/) — note the exact `(owner, repo)` and skill name.
2. Edit `registry.json`:
   - Add `{name, owner, repo, role}` to `skills[]` (alphabetical position is fine).
   - Bump `count`, `version`, and `generated_at`.
3. `./install.sh --dry-run` then `./validate-registry.sh`.
4. Commit and push — CI runs both checks automatically.

## Continuous integration

Two GitHub Actions workflows under `.github/workflows/`:

- **`validate-registry.yml`** — runs on every push/PR touching `registry.json`, `install.sh`, `validate-registry.sh`, or itself. Steps: registry integrity check, install.sh dry-run smoke test, and a Python assertion that every non-TBD entry was actually planned by the dry-run output.
- **`verify-upstreams.yml`** — scheduled weekly (Mondays 06:00 UTC) + manual dispatch. Checks every `(owner, repo)` still publishes the referenced `SKILL.md` via the GitHub contents API (with raw.githubusercontent fallback). Catches silent upstream removals before they break `./install.sh`.

## Layout

```
.
├── README.md
├── registry.json          # 30 entries (the source of truth)
├── install.sh             # wipe (gitignore-respecting) + install
├── validate-registry.sh   # integrity check (count, roles, duplicates)
├── .gitignore             # excludes /[REMOVED-INTERNAL-SKILL]/, /[REMOVED-INTERNAL-SKILL]/, etc. + stray install artifacts
├── <skill-name>/          # one directory per installed skill, at the root
└── .github/workflows/
    ├── validate-registry.yml
    └── verify-upstreams.yml
```

## `.gitignore` rationale

`/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-MARKER]/`, `/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-SKILL]/`, `/[REMOVED-INTERNAL-SKILL]/` are private/custom skills not part of the public distribution — preserved on wipe.

`/.agents/`, `/.claude/` and `/skills-lock.json` are project-scoped `npx skills add` artifacts. Installs go global (`-g`) straight into the repo root, so these should never reappear; `./install.sh` deletes them on every run as a safety net.
