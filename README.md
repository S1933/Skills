# Skills

A personal collection of [Agent Skills](https://agentskills.io/specification) for Claude Code. Each subdirectory is one skill with a `SKILL.md` (plus optional supporting files). Skills marked **(manual)** set `disable-model-invocation: true` — they run only when you invoke them explicitly (e.g. `/grilling`); the rest can auto-trigger from their description.

## Planning & specification

| Skill | When to use |
|---|---|
| [brainstorming](brainstorming/) | Before any creative work — explore intent, requirements, and design before implementing. |
| [grilling](grilling/) | Stress-test a plan or design with a relentless one-question-at-a-time interview. |
| [grill-me](grill-me/) **(manual)** | Thin wrapper that runs a `/grilling` session. |
| [grill-with-docs](grill-with-docs/) **(manual)** | `/grilling` that also produces ADRs + glossary via `/domain-modeling`. |
| [writing-plans](writing-plans/) | Turn a spec into a written multi-step implementation plan before touching code. |
| [executing-plans](executing-plans/) **(manual)** | Execute a written plan in a separate session with review checkpoints. |
| [to-prd](to-prd/) **(manual)** | Synthesize the current conversation into a PRD on the issue tracker. |
| [to-issues](to-issues/) **(manual)** | Break a plan/PRD into independently-grabbable, vertically-sliced issues. |
| [request-refactor-plan](request-refactor-plan/) | Interview into a tiny-commit refactor plan, filed as a GitHub issue. |
| [decision-mapping](decision-mapping/) **(manual)** | Turn a loose idea into a sequenced map of investigation tickets. |
| [handoff](handoff/) **(manual)** | Compact the conversation into a handoff doc for a fresh agent. |
| [prototype](prototype/) **(manual)** | Build a throwaway prototype to flesh out a design. |

## Implementation & execution

| Skill | When to use |
|---|---|
| [implement](implement/) **(manual)** | Implement work from a PRD/issues using canonical TDD, verification, and code-review skills. |
| [test-driven-development](test-driven-development/) | Any feature/bugfix — test first, watch it fail, minimal code, refactor. |
| [subagent-driven-development](subagent-driven-development/) | Execute plans with independent tasks in the current session. |
| [dispatching-parallel-agents](dispatching-parallel-agents/) | 2+ independent tasks with no shared state or sequencing. |
| [using-git-worktrees](using-git-worktrees/) | Isolate feature work in a dedicated workspace. |
| [migrate-to-shoehorn](migrate-to-shoehorn/) | Replace `as` type assertions in tests with `@total-typescript/shoehorn`. |
| [setup-pre-commit](setup-pre-commit/) | Add Husky + lint-staged pre-commit hooks (format/typecheck/test). |

## Debugging

| Skill | When to use |
|---|---|
| [systematic-debugging](systematic-debugging/) | Any bug, test failure, or unexpected behavior — before proposing fixes. |

## Code review & shipping

| Skill | When to use |
|---|---|
| [review-scope](review-scope/) | Gather the full diff (base branch + all layers) — a building block for reviews. |
| [requesting-code-review](requesting-code-review/) | Dispatch a reviewer subagent with crafted context. |
| [receiving-code-review](receiving-code-review/) | Respond to review feedback with rigor, not performative agreement. |
| [verification-before-completion](verification-before-completion/) | Before claiming done — run verification and show evidence. |
| [resolving-merge-conflicts](resolving-merge-conflicts/) | Resolve an in-progress merge/rebase conflict. |
| [finishing-a-development-branch](finishing-a-development-branch/) | Decide how to integrate finished work (merge/PR/cleanup). |

## Codebase audit & architecture

| Skill | When to use |
|---|---|
| [improve](improve/) | Read-only senior-advisor survey → self-contained handoff plans for other agents. |
| [tech-debt-audit](tech-debt-audit/) **(manual)** | One broad debt report (`TECH_DEBT_AUDIT.md`) committed to the repo. |
| [improve-codebase-architecture](improve-codebase-architecture/) **(manual)** | Architecture-depth-only deepening opportunities as a visual HTML report. |
| [codebase-design](codebase-design/) | Shared vocabulary for designing deep modules, seams, and interfaces. |
| [domain-modeling](domain-modeling/) | Build/sharpen a project's domain model and record decisions. |
| [ubiquitous-language](ubiquitous-language/) **(manual)** | Extract a DDD glossary (`UBIQUITOUS_LANGUAGE.md`) from the conversation. |
| [design-an-interface](design-an-interface/) | Generate radically different interface designs via parallel sub-agents. |

> The audit trio is deliberately distinct: **improve** = handoff plans for another agent · **tech-debt-audit** = one broad report file · **improve-codebase-architecture** = architecture-only HTML report.

## Reusable craft patterns (Go / systems)

| Skill | When to use |
|---|---|
| [go-cli-conventions](go-cli-conventions/) | Building/reviewing Go 1.24+ CLIs (Cobra, flags, exit behavior, config). |
| [adapter-pattern](adapter-pattern/) | Interoperate with multiple external APIs/providers without leaking vendor details. |
| [atomic-file-write](atomic-file-write/) | Replace config/state/user files safely against crashes and partial writes. |
| [schema-validation](schema-validation/) | Validate config/payloads/manifests with cross-field invariants and clear errors. |
| [golden-file-testing](golden-file-testing/) | Test generated text/config/serialization whose full shape matters. |
| [embedded-fixtures](embedded-fixtures/) | Package templates/schemas/fixtures with the binary via Go embed. |
| [binary-distribution](binary-distribution/) | Release compiled CLIs across OS/arch (archives, checksums, signing, installers). |

## Issue triage & QA

| Skill | When to use |
|---|---|
| [qa](qa/) | Conversational bug reporting that files GitHub issues with codebase context. |
| [triage](triage/) **(manual)** | Move issues through a triage state machine into agent-ready briefs. |

## Private and environment-specific

These skills are kept under `private-skills/` so public-only installations can
exclude them. Their machine-specific values belong in the ignored
`.local/skills-environment.yaml` file.

| Skill | When to use |
|---|---|
| [[REMOVED-INTERNAL-SKILL]](private-skills/[REMOVED-INTERNAL-SKILL]/) | OVH [REMOVED-INTERNAL-SKILL] CI/CD — authoring/validating `.cds/` YAML. |
| [[REMOVED-INTERNAL-SKILL]](private-skills/[REMOVED-INTERNAL-SKILL]/) | Fix/update smoke-test patterns for www.[redacted-infrastructure].com. |
| [[REMOVED-INTERNAL-SKILL]](private-skills/[REMOVED-INTERNAL-SKILL]/) | Manage [REMOVED-INTERNAL-SKILL] issues via a locally configured `[REMOVED-INTERNAL-SKILL]` CLI. |
| [[REMOVED-INTERNAL-SKILL]](private-skills/[REMOVED-INTERNAL-SKILL]/) | Sync local files to a configured development server via the `rr` function. |

## Meta & tooling

| Skill | When to use |
|---|---|
| [writing-skills](writing-skills/) | Create, edit, or verify skills. |
| [using-superpowers](using-superpowers/) **(manual)** | How to find and use skills at the start of a conversation. |
| [git-guardrails-claude-code](git-guardrails-claude-code/) | Hooks that block dangerous git commands before they run. |
| [codex](codex/) | Get a second opinion / verification / deep research via the Codex CLI. |
| [caveman](caveman/) | Ultra-compressed communication mode (~75% fewer tokens). |

---

## Conventions

- **Frontmatter**: unquoted `name` + `description` (quote only when YAML requires it). `description` is third-person and states *when* to use the skill.
- **Provenance**: attribution (`license`, `metadata.author`) is set only where the upstream author is known (e.g. `improve` — shadcn, MIT). Much of the planning/review/TDD set originates from the [superpowers](https://github.com/obra/superpowers) collection.
- See [writing-skills](writing-skills/) for the full authoring standard.
