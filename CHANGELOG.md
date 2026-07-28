# Changelog

This project uses repository-level tagged releases. Changes are grouped by skill or catalogue subsystem.

## Unreleased

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
