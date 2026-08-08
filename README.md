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

## Public skills (11)

| Skill | Invocation | Clients | Description |
|---|---|---|---|
| [`adapter-pattern`](adapter-pattern/) | automatic | agent-skills | Use when one domain model must interoperate with multiple external APIs, file formats, providers, CLIs, storage engines, or versioned protocols without leaking vendor details into core logic. |
| [`atomic-file-write`](atomic-file-write/) | automatic | agent-skills | Use when replacing configuration, state, generated, or user-owned files where crashes, partial writes, permissions, concurrent readers, or durability can corrupt observable state. |
| [`binary-distribution`](binary-distribution/) | automatic | agent-skills | Use when releasing compiled command-line tools across operating systems or architectures, including version metadata, archives, checksums, signing, installers, and reproducible release automation. |
| [`codex`](codex/) | automatic | codex | Use when an independent technical second opinion, verification, repository analysis, or deeper library or API research would materially reduce uncertainty. |
| [`embedded-fixtures`](embedded-fixtures/) | automatic | agent-skills | Use when binaries or tests need deterministic templates, schemas, migrations, defaults, or sample files packaged with the executable through Go embed or an equivalent resource mechanism. |
| [`go-cli-conventions`](go-cli-conventions/) | automatic | agent-skills | Use when creating, extending, or reviewing Go 1.24+ command-line applications, especially Cobra commands, flags, exit behavior, configuration, and testable CLI boundaries. |
| [`golden-file-testing`](golden-file-testing/) | automatic | agent-skills | Use when testing generated text, configuration, serialization, templates, compiler output, or other stable artifacts whose complete shape matters more than isolated fields. |
| [`repository-reconnaissance`](repository-reconnaissance/) | automatic | agent-skills | Use when an audit, review, plan, or unfamiliar repository task needs an evidence-based map of instructions, architecture, commands, history, and inspectable scope before conclusions are drawn. |
| [`review-scope`](review-scope/) | automatic | agent-skills | Use when beginning a code review that must include committed, staged, unstaged, and relevant untracked changes against the correct base. |
| [`[REMOVED-INTERNAL-SKILL]`]([REMOVED-INTERNAL-SKILL]/) | automatic | agent-skills | Use when integrating the Scaleflex, Filerobot, or Cloudimage API — searching DAM assets by metadata, uploading files, running Visual AI models, or invalidating CDN cache. |
| [`schema-validation`](schema-validation/) | automatic | agent-skills | Use when defining or reviewing validation for configuration files, API payloads, manifests, serialized models, cross-field invariants, or human-readable validation errors. |

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
python3 scripts/generate-catalogue.py --check
python3 scripts/generate-dependency-graph.py --check
python3 scripts/validate-evals.py
python3 scripts/validate-skills.py
git ls-files '*.sh' '*.zsh' | xargs shellcheck
```

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for licensing and adapted upstream material.
