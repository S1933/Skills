# Notices and provenance

The root MIT licence covers original catalogue material and local modifications. Adapted third-party portions retain their upstream notices and terms.

Full retained licence texts are in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

## Superpowers

- Upstream: [obra/superpowers](https://github.com/obra/superpowers)
- Original author: Jesse Vincent and contributors
- Licence: MIT, copyright 2025 Jesse Vincent
- Adapted areas include brainstorming, planning, worktree, TDD, debugging, review, subagent-development, verification, branch-finishing, and skill-authoring workflows.
- Local changes include safety hardening, client metadata, dependency declarations, progressive disclosure, validation, and behavioural evaluation fixtures.

## Improve

- Upstream attribution recorded in the adapted skill: shadcn
- Upstream project: [shadcn/improve](https://github.com/shadcn/improve)
- Licence: MIT, copyright 2026 shadcn
- Local changes include evidence/safety contracts, progressive disclosure, and catalogue integration.

The repository no longer retains vendored copies of upstream skills. Skills are
installed dynamically from their canonical upstream sources (see
[`docs/migration-npx.md`](docs/migration-npx.md) and
[`external-skills.yaml`](external-skills.yaml)); their licence and attribution
remain with their upstream repositories.

Contributors must add or update this notice whenever adapting material from
another source and must preserve any source-level licence or attribution
metadata.
