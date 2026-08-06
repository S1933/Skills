# Changelog

This project uses repository-level tagged releases. Changes are grouped by skill or catalogue subsystem.

## Unreleased

### Migration

- Migrated the 31 selected third-party skills to their canonical upstream sources loaded dynamically via `npx skills` (15 from `mattpocock/skills`, 4 from `obra/superpowers`, 1 from `ksimback/tech-debt-skill`, 11 maintained here in `S1933/skills`).
- Removed the 38 historical vendored copies (brainstorming, caveman, codebase-design, decision-mapping, design-an-interface, dispatching-parallel-agents, domain-modeling, executing-plans, finishing-a-development-branch, git-guardrails-claude-code, grill-me, grill-with-docs, grilling, handoff, implement, improve, improve-codebase-architecture, migrate-to-shoehorn, prototype, qa, receiving-code-review, request-refactor-plan, requesting-code-review, resolving-merge-conflicts, setup-pre-commit, subagent-driven-development, systematic-debugging, tech-debt-audit, test-driven-development, to-issues, to-prd, triage, ubiquitous-language, using-git-worktrees, using-superpowers, verification-before-completion, writing-plans, writing-skills) from the repository and manifest.
- Kept the 11 site-maintained skills (adapter-pattern, atomic-file-write, binary-distribution, codex, embedded-fixtures, go-cli-conventions, golden-file-testing, repository-reconnaissance, review-scope, [REMOVED-INTERNAL-SKILL], schema-validation) plus the 4 private skills ([REMOVED-INTERNAL-SKILL], [REMOVED-INTERNAL-SKILL], [REMOVED-INTERNAL-SKILL], [REMOVED-INTERNAL-SKILL]).
- Regenerated `README.md`, `docs/generated/catalogue.md`, and `docs/generated/dependency-graph.md` from the manifest.
- See `docs/migration-npx.md` for the rollout procedure and rollback notes.

### Security

- Made Codex second-opinion execution read-only and sandboxed by default.
- Hardened Git guardrails with fail-closed parsing and command fixtures.
- Separated and sanitized environment-specific skills.

### Catalogue

- Added a complete manifest, dependency declarations, generated documentation, compatibility metadata, and canonical aliases policy.
- Added shared reconnaissance, evidence, and execution-safety contracts.
- Refactored oversized skills for progressive disclosure and enforced an 800-word main-file ceiling.

### Validation and evaluation

- Added repository, frontmatter, reference, example, shell, dependency, privacy, size, and compatibility validation.
- Added CI, validator unit tests, guardrail/Codex regressions, trigger suites, behavior suites, and metrics scoring.

## Release policy

- Tag catalogue releases using semantic versioning.
- Use patch releases for guidance fixes and compatible metadata changes.
- Use minor releases for new skills, evaluation formats, or optional capabilities.
- Use major releases for incompatible invocation, manifest, installation, or behavior-contract changes.
- Per-skill versions are optional and reserved for skills consumed independently outside this catalogue.
