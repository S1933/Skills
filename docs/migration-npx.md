# Migration of skills to dynamic npx sources

This migration replaces the historical vendored copies of skills previously
installed from `S1933/skills` with a selection fetched directly from their
canonical upstream repositories.

## Resulting selection

- 15 skills from `mattpocock/skills`;
- 4 skills from `obra/superpowers`;
- 1 skill from `ksimback/tech-debt-skill`;
- 1 skill from `ayghri/i-have-adhd`;
- 1 skill from `juliusbrussee/caveman`;
- 11 skills maintained in `S1933/skills`;
- global installation scoped to the target agent;
- **33 skills installed for `claude-code`; 32 for `codex`, `opencode`, and `cursor`**
  (22 externals + 11 maintained locally, minus the Claude-Code-only
  `tech-debt-audit` on the other three agents).

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
A skill that is absent is simply ignored.

The `--agent` value selects the target agent store. The catalogue targets the
four mainstream clients, so every install/remove command below must run once per
agent rather than once for `universal` (which maps to a neutral store that none
of these clients load). Define the target set once per shell session:

```bash
AGENTS="claude-code codex opencode cursor"
```

```bash
for agent in $AGENTS; do \
  npx --yes skills@latest remove --global \
    --agent "$agent" \
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
    --skill writing-skills --yes; \
done
```

## 4. Install Matt Pocock skills (15)

```bash
for agent in $AGENTS; do \
  npx --yes skills@latest add mattpocock/skills --global --copy \
    --agent "$agent" \
    --skill setup-matt-pocock-skills --skill grilling --skill domain-modeling \
    --skill grill-with-docs --skill to-spec --skill to-tickets --skill triage \
    --skill tdd --skill diagnosing-bugs --skill code-review \
    --skill codebase-design --skill improve-codebase-architecture \
    --skill writing-for-agents --skill handoff --skill wait-what --yes; \
done
```

## 5. Install Superpowers skills (4)

```bash
for agent in $AGENTS; do \
  npx --yes skills@latest add obra/superpowers --global --copy \
    --agent "$agent" \
    --skill dispatching-parallel-agents --skill receiving-code-review \
    --skill verification-before-completion \
    --skill finishing-a-development-branch --yes; \
done
```

## 6. Install the technical-debt audit skill (1)

This skill declares itself Claude-Code-only (`claude_code_only: true` in
`external-skills.yaml`): it relies on TodoWrite and the Task tool, which are
not available in the other agents. Install it for `claude-code` only.

```bash
npx --yes skills@latest add ksimback/tech-debt-skill --global --copy \
  --agent claude-code --skill tech-debt-audit --yes
```

## 7. Install i-have-adhd (1)

Manually-invoked communication style for ADHD readers: lead with action, number
steps, suppress tangents, restate state. Installable as a normal `npx skills add`
target (verified at https://skills.sh/ayghri/i-have-adhd).

```bash
for agent in $AGENTS; do \
  npx --yes skills@latest add ayghri/i-have-adhd --global --copy \
    --agent "$agent" --skill i-have-adhd --yes; \
done
```

## 8. Install caveman (1)

Ultra-compressed communication mode (65% token reduction). Note: upstream
allows auto-triggering when token efficiency is requested; can conflict with
`i-have-adhd` (both are persistent formatting modes). Supports lite / full /
ultra / wenyan intensity levels. Installable as a normal
`npx skills add` target (verified at https://skills.sh/juliusbrussee/caveman/caveman).

```bash
for agent in $AGENTS; do \
  npx --yes skills@latest add juliusbrussee/caveman --global --copy \
    --agent "$agent" --skill caveman --yes; \
done
```

## 9. Install the S1933/skills-specific skills (11)

The explicit selection avoids installing the old third-party copies that are
still present on the `improve/skills-catalogue` branch.

```bash
for agent in $AGENTS; do \
  npx --yes skills@latest add S1933/skills --global --copy \
    --agent "$agent" \
    --skill adapter-pattern --skill atomic-file-write --skill binary-distribution \
    --skill codex --skill embedded-fixtures --skill go-cli-conventions \
    --skill golden-file-testing --skill repository-reconnaissance \
    --skill review-scope --skill [REMOVED-INTERNAL-SKILL] --skill schema-validation --yes; \
done
```

## 10. Verify the installation

```bash
for agent in $AGENTS; do \
  echo "== $agent =="; \
  npx --yes skills@latest list --global --agent "$agent"; \
done
```

Check notably for the presence of:

- `tdd`, `diagnosing-bugs` and `code-review`;
- `triage`, `to-spec` and `to-tickets`;
- `dispatching-parallel-agents` and `verification-before-completion`;
- `tech-debt-audit` (**only under `claude-code`**; absent on the other three
  agents, by design);
- `repository-reconnaissance`, `review-scope` and `[REMOVED-INTERNAL-SKILL]`.

`claude-code` should show **33** skills added by this migration; `codex`,
`opencode`, and `cursor` should each show **32** (the difference is the
Claude-Code-only `tech-debt-audit`).

## Later updates

A bare `npx skills update --global` updates every global skill, including ones
outside this catalogue's declared selection. Prefer replaying the six `add`
commands above (steps 4-9): invoking `add` with the same source, pin `--agent`,
and the same `--skill` selection is idempotent and refreshes only the declared
selection (33 for `claude-code`, 32 for the other three agents). Re-running
add with the same source and skill selection is idempotent; it overwrites
already-present files automatically.

```bash
npx --yes skills@latest update --global --yes
```

A bare `update --global` refreshes every installed skill including ones
outside this catalogue's declared selection. Prefer the `add` commands above
when the declared selection changes. After updating, re-verify per-agent
counts (33 / 32 / 32 / 32) — `update` does not introduce `tech-debt-audit`
on non-claude-code agents.

Re-run the six `add` commands if the declared selection changes or if a skill
is renamed upstream. The `verified_commit` fields in `external-skills.yaml`
record the upstream revision at the time of the last audit; they are not a
reproducibility mechanism (the CLI installs from the default branch, and
`owner/repo#SHA` is not supported). For a truly immutable install, pin a
local checkout at the audited commit.

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
names listed in that inventory.

The historical vendored copies are preserved on the `recovery/pre-migration`
branch, cut from `7c15432d909107e0ea59b149cfce538174d34392` (the last commit
before the migration). Recover them with:

```bash
git fetch origin recovery/pre-migration:recovery/pre-migration
git checkout recovery/pre-migration
```

If a `recovery/pre-migration` branch does not yet exist on the remote, create it
from the referenced commit before relying on this procedure:

```bash
git branch recovery/pre-migration 7c15432d909107e0ea59b149cfce538174d34392
git push origin recovery/pre-migration
```
