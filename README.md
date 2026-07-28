<!-- Generated from skills-manifest.yaml; do not edit manually. -->

# Skills catalogue

A validated catalogue of portable and client-specific Agent Skills. The repository is in stabilization mode: improve existing skills and safety/evaluation coverage before proposing new functional skills.

- [Installation](docs/installation.md)
- [Authoring standard](docs/skill-authoring-standard.md)
- [Contributing](CONTRIBUTING.md)
- [Detailed generated catalogue](docs/generated/catalogue.md)
- [Dependency graph](docs/generated/dependency-graph.md)
- [Evaluation format](docs/evaluations.md)
- [Provenance](NOTICE.md)

## Public skills (48)

| Skill | Invocation | Clients | Description |
|---|---|---|---|
| [`adapter-pattern`](adapter-pattern/) | automatic | agent-skills | Use when one domain model must interoperate with multiple external APIs, file formats, providers, CLIs, storage engines, or versioned protocols without leaking vendor details into core logic. |
| [`atomic-file-write`](atomic-file-write/) | automatic | agent-skills | Use when replacing configuration, state, generated, or user-owned files where crashes, partial writes, permissions, concurrent readers, or durability can corrupt observable state. |
| [`binary-distribution`](binary-distribution/) | automatic | agent-skills | Use when releasing compiled command-line tools across operating systems or architectures, including version metadata, archives, checksums, signing, installers, and reproducible release automation. |
| [`brainstorming`](brainstorming/) | automatic | agent-skills | Use when creating features, components, functionality, or any behaviour change that requires intent and design to be clarified before implementation. |
| [`caveman`](caveman/) | automatic | agent-skills | Use when the user explicitly requests caveman mode, ultra-compressed responses, fewer tokens, or unusually terse technical communication. |
| [`codebase-design`](codebase-design/) | automatic | agent-skills | Use when designing or improving module interfaces, seams, information hiding, testability, navigability, or deep-module boundaries. |
| [`codex`](codex/) | automatic | codex | Use when an independent technical second opinion, verification, repository analysis, or deeper library or API research would materially reduce uncertainty. |
| [`decision-mapping`](decision-mapping/) | manual | agent-skills | Use when explicitly invoking /decision-mapping to turn a loose idea into sequenced investigation tickets whose findings drive later decisions. |
| [`design-an-interface`](design-an-interface/) | automatic | claude-code, codex, opencode | Use when exploring multiple substantially different API or module-interface designs before choosing one. |
| [`dispatching-parallel-agents`](dispatching-parallel-agents/) | automatic | claude-code, codex, opencode | Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies |
| [`domain-modeling`](domain-modeling/) | automatic | agent-skills | Use when defining domain terminology, ubiquitous language, bounded contexts, or architectural decisions tied to a domain model. |
| [`embedded-fixtures`](embedded-fixtures/) | automatic | agent-skills | Use when binaries or tests need deterministic templates, schemas, migrations, defaults, or sample files packaged with the executable through Go embed or an equivalent resource mechanism. |
| [`executing-plans`](executing-plans/) | manual | agent-skills | Use when explicitly invoking /executing-plans with an approved implementation plan in a separate session. |
| [`finishing-a-development-branch`](finishing-a-development-branch/) | automatic | agent-skills | Use when implementation and verification are complete and the branch needs an explicit merge, pull-request, retention, or cleanup decision. |
| [`git-guardrails-claude-code`](git-guardrails-claude-code/) | automatic | claude-code | Use when setting up Claude Code hooks to prevent pushes or destructive Git operations from running without user control. |
| [`go-cli-conventions`](go-cli-conventions/) | automatic | agent-skills | Use when creating, extending, or reviewing Go 1.24+ command-line applications, especially Cobra commands, flags, exit behavior, configuration, and testable CLI boundaries. |
| [`golden-file-testing`](golden-file-testing/) | automatic | agent-skills | Use when testing generated text, configuration, serialization, templates, compiler output, or other stable artifacts whose complete shape matters more than isolated fields. |
| [`grill-me`](grill-me/) | manual | agent-skills | Use when explicitly invoking /grill-me to stress-test and sharpen a plan or design. |
| [`grill-with-docs`](grill-with-docs/) | manual | agent-skills | Use when explicitly invoking /grill-with-docs to stress-test a plan while recording ADRs and a domain glossary. |
| [`grilling`](grilling/) | automatic | agent-skills | Use when a plan or design needs a rigorous one-question-at-a-time stress test before implementation. |
| [`handoff`](handoff/) | manual | agent-skills | Use when explicitly preparing the current conversation for another agent to continue with minimal context loss. |
| [`implement`](implement/) | manual | claude-code, codex, opencode | Use when explicitly implementing work from an approved PRD, specification, or issue set. |
| [`improve`](improve/) | automatic | agent-skills | Use when surveying a codebase for prioritized improvement opportunities across correctness, security, performance, testing, maintainability, developer experience, migrations, or product direction. |
| [`improve-codebase-architecture`](improve-codebase-architecture/) | manual | agent-skills | Use when explicitly auditing a codebase for deep-module, seam, interface, or information-hiding opportunities in an architecture-focused visual report. |
| [`migrate-to-shoehorn`](migrate-to-shoehorn/) | automatic | agent-skills | Use when TypeScript tests use as assertions for partial fixtures and should migrate to @total-typescript/shoehorn. |
| [`prototype`](prototype/) | manual | agent-skills | Use when explicitly building a throwaway prototype to answer design questions about business logic, state transitions, or alternative user interfaces. |
| [`qa`](qa/) | automatic | agent-skills | Use when the user wants a conversational QA session to report, investigate, and file reproducible software issues. |
| [`receiving-code-review`](receiving-code-review/) | automatic | agent-skills | Use when review feedback must be understood, verified, prioritized, or challenged before implementation. |
| [`repository-reconnaissance`](repository-reconnaissance/) | automatic | agent-skills | Use when an audit, review, plan, or unfamiliar repository task needs an evidence-based map of instructions, architecture, commands, history, and inspectable scope before conclusions are drawn. |
| [`request-refactor-plan`](request-refactor-plan/) | automatic | agent-skills | Use when planning a risky or substantial refactor as safe incremental commits and a reviewable issue or RFC. |
| [`requesting-code-review`](requesting-code-review/) | automatic | claude-code, codex, opencode | Use when implementation work needs an independent code review before completion, integration, or merge. |
| [`resolving-merge-conflicts`](resolving-merge-conflicts/) | automatic | agent-skills | Use when you need to resolve an in-progress git merge/rebase conflict. |
| [`review-scope`](review-scope/) | automatic | agent-skills | Use when beginning a code review that must include committed, staged, unstaged, and relevant untracked changes against the correct base. |
| [`schema-validation`](schema-validation/) | automatic | agent-skills | Use when defining or reviewing validation for configuration files, API payloads, manifests, serialized models, cross-field invariants, or human-readable validation errors. |
| [`setup-pre-commit`](setup-pre-commit/) | automatic | agent-skills | Use when adding or repairing Husky pre-commit automation for formatting, type checking, and tests in a JavaScript or TypeScript repository. |
| [`subagent-driven-development`](subagent-driven-development/) | automatic | claude-code, codex, opencode | Use when executing implementation plans with independent tasks in the current session |
| [`systematic-debugging`](systematic-debugging/) | automatic | agent-skills | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes |
| [`tech-debt-audit`](tech-debt-audit/) | manual | agent-skills | Use when explicitly requesting a broad repository-wide technical-debt, architecture, or code-health audit delivered as one evidence-backed report. |
| [`test-driven-development`](test-driven-development/) | automatic | agent-skills | Use when implementing any feature or bugfix, before writing implementation code |
| [`to-issues`](to-issues/) | manual | agent-skills | Use when explicitly converting an approved plan, specification, or PRD into independently assignable vertical-slice issues. |
| [`to-prd`](to-prd/) | manual | agent-skills | Use when explicitly publishing requirements already established in conversation as a PRD without another discovery interview. |
| [`triage`](triage/) | manual | agent-skills | Use when explicitly moving issue reports through categorisation, reproduction, clarification, and agent-ready briefing. |
| [`ubiquitous-language`](ubiquitous-language/) | manual | agent-skills | Use when explicitly extracting or refining canonical domain terminology, definitions, ambiguities, and discouraged synonyms from the conversation. |
| [`using-git-worktrees`](using-git-worktrees/) | automatic | agent-skills | Use when implementation work needs an isolated Git workspace or when an execution workflow requires isolation before changes begin. |
| [`using-superpowers`](using-superpowers/) | manual | agent-skills | Use when explicitly invoking /using-superpowers at the start of a conversation where repository skills are available. |
| [`verification-before-completion`](verification-before-completion/) | automatic | agent-skills | Use when about to claim work is complete, fixed, passing, ready to commit, or ready to merge. |
| [`writing-plans`](writing-plans/) | automatic | agent-skills | Use when you have a spec or requirements for a multi-step task, before touching code |
| [`writing-skills`](writing-skills/) | automatic | agent-skills | Use when creating new skills, editing existing skills, or verifying skills work before deployment |

## Private/environment-specific skills (4)

Private skills remain in the repository for local use but are excluded from public-only installation guidance and may require `.local/skills-environment.yaml`.

| Skill | Invocation | Clients | Description |
|---|---|---|---|
| [`[REMOVED-INTERNAL-SKILL]`](private-skills/[REMOVED-INTERNAL-SKILL]/) | automatic | local-shell | Use when authoring, reviewing, testing, troubleshooting, or migrating OVH [REMOVED-INTERNAL-SKILL] workflow, action, worker-model, template, gate, matrix, service, or expression YAML. |
| [`[REMOVED-INTERNAL-SKILL]`](private-skills/[REMOVED-INTERNAL-SKILL]/) | automatic | local-shell | Use when a locally configured [REMOVED-INTERNAL-SKILL] CLI is required to inspect or mutate issues, comments, assignments, transitions, Tempo entries, or Confluence pages. |
| [`[REMOVED-INTERNAL-SKILL]`](private-skills/[REMOVED-INTERNAL-SKILL]/) | automatic | local-shell | Use when [redacted-infrastructure] smoke-test patterns fail literal HTML matching or the locale-specific pattern catalogue needs updating. |
| [`[REMOVED-INTERNAL-SKILL]`](private-skills/[REMOVED-INTERNAL-SKILL]/) | automatic | local-shell | Use when syncing local project files to a configured development server through the rr Zsh function, or when rr produces unexpected results. |

## Validate

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover --start-directory tests --pattern 'test_*.py'
python3 -m unittest discover --start-directory git-guardrails-claude-code/tests --pattern 'test_*.py'
git-guardrails-claude-code/tests/test-guardrail.sh
python3 scripts/generate-catalogue.py --check
python3 scripts/generate-dependency-graph.py --check
python3 scripts/validate-evals.py
python3 scripts/validate-skills.py
git ls-files '*.sh' '*.zsh' | xargs shellcheck
```

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for licensing and adapted upstream material.
