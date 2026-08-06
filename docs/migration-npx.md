# Migration of skills to dynamic npx sources

This migration replaces the historical vendored copies of skills previously
installed from `S1933/skills` with a selection fetched directly from their
canonical upstream repositories.

## Resulting selection

- 15 skills from `mattpocock/skills`;
- 4 skills from `obra/superpowers`;
- 1 skill from `ksimback/tech-debt-skill`;
- 11 skills maintained in `S1933/skills`;
- global installation scoped to the target agent;
- **31 skills installed in total**.

The four private skills of `S1933/skills` (`[REMOVED-INTERNAL-SKILL]`, `[REMOVED-INTERNAL-SKILL]`, `[REMOVED-INTERNAL-SKILL]`,
`[REMOVED-INTERNAL-SKILL]`) are **not** installed by this migration.

## 1. Prerequisites

Requires Node.js, npm and npx. Does not require `gh`.

```bash
node --version
npm --version
npx --yes skills@latest --version
```

## 2. Save the current inventory

```bash
npx --yes skills@latest list --global --json > skills-before-migration.json
```

## 3. Remove the old copies

Removal is limited to the 38 names historically versioned in `S1933/skills`.
A skill that is absent is simply ignored. The `--agent` value selects the
target agent store (`universal` for a neutral store, or `claude-code`,
`codex`, `opencode`, `cursor` on a machine where those agents exist).

```bash
npx --yes skills@latest remove --global \
  --agent universal \
  --skill brainstorming --skill caveman --skill codebase-design \
  --skill decision-mapping --skill design-an-interface \
  --skill dispatching-parallel-agents --skill domain-modeling \
  --skill executing-plans --skill finishing-a-development-branch \
  --skill git-guardrails-claude-code --skill grill-me --skill grill-with-docs \
  --skill grilling --skill handoff --skill implement --skill improve \
  --skill improve-codebase-architecture --skill migrate-to-shoehorn \
  --skill prototype --skill qa --skill receiving-code-review \
  --skill request-refactor-plan --skill requesting-code-review \
  --skill resolving-merge-conflicts --skill setup-pre-commit \
  --skill subagent-driven-development --skill systematic-debugging \
  --skill tech-debt-audit --skill test-driven-development --skill to-issues \
  --skill to-prd --skill triage --skill ubiquitous-language \
  --skill using-git-worktrees --skill using-superpowers \
  --skill verification-before-completion --skill writing-plans \
  --skill writing-skills --yes
```

## 4. Install Matt Pocock skills (15)

```bash
npx --yes skills@latest add mattpocock/skills --global --copy \
  --agent universal \
  --skill setup-matt-pocock-skills --skill grilling --skill domain-modeling \
  --skill grill-with-docs --skill to-spec --skill to-tickets --skill triage \
  --skill tdd --skill diagnosing-bugs --skill code-review \
  --skill codebase-design --skill improve-codebase-architecture \
  --skill writing-for-agents --skill handoff --skill wait-what --yes
```

## 5. Install Superpowers skills (4)

```bash
npx --yes skills@latest add obra/superpowers --global --copy \
  --agent universal \
  --skill dispatching-parallel-agents --skill receiving-code-review \
  --skill verification-before-completion \
  --skill finishing-a-development-branch --yes
```

## 6. Install the technical-debt audit skill (1)

```bash
npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \
  --agent universal --skill tech-debt-audit --yes
```

## 7. Install the S1933/skills-specific skills (11)

The explicit selection avoids installing the old third-party copies that are
still present in the current remote branch.

```bash
npx --yes skills@latest add S1933/skills --global --copy \
  --agent universal \
  --skill adapter-pattern --skill atomic-file-write --skill binary-distribution \
  --skill codex --skill embedded-fixtures --skill go-cli-conventions \
  --skill golden-file-testing --skill repository-reconnaissance \
  --skill review-scope --skill [REMOVED-INTERNAL-SKILL] --skill schema-validation --yes
```

## 8. Verify the installation

```bash
npx --yes skills@latest list --global --agent universal
```

Check notably for the presence of:

- `tdd`, `diagnosing-bugs` and `code-review`;
- `triage`, `to-spec` and `to-tickets`;
- `dispatching-parallel-agents` and `verification-before-completion`;
- `tech-debt-audit`;
- `repository-reconnaissance`, `review-scope` and `[REMOVED-INTERNAL-SKILL]`.

## Later updates

To fetch the latest versions of already-installed global skills:

```bash
npx --yes skills@latest update --global --yes
```

Re-run the four `add` commands if the declared selection changes or if a skill
is renamed upstream.

## Voluntary exclusions

- `improve` is not reinstalled, as it largely overlaps `tech-debt-audit` and
  `improve-codebase-architecture`.
- The Superpowers workflows `test-driven-development`,
  `systematic-debugging` and `requesting-code-review` are replaced by the Matt
  Pocock skills `tdd`, `diagnosing-bugs` and `code-review`.
- `using-git-worktrees` is not installed globally, as its project
  configuration assumptions do not suit every stack and package manager.
- Deprecated Matt Pocock names are not kept as local snapshots.

## Rollback

`skills-before-migration.json` keeps only the initial inventory; it does not
contain the skill files. To roll back, reinstall explicitly the sources and
names listed in that inventory. In this repository, the historical vendored
copies remain recoverable from the `recovery/pre-migration` branch.
