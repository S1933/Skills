---
name: writing-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment
---

# Writing Skills

Treat skill guidance as executable behavior, not prose documentation. Apply the `test-driven-development` cycle to the prompts that should activate the skill and to the behavior the skill must change.

## Iron law

Do not publish a skill change without first observing a relevant evaluation fail. A skill that merely reads well is unverified.

## Core workflow

1. **Classify the skill.** Decide whether it is a thin wrapper, technique, pattern, workflow, or reference. This determines its size budget and evaluation style.
2. **Define activation.** Write positive, negative, ambiguous, and collision prompts before editing the description. Descriptions contain observable triggers only and start with `Use when`.
3. **RED.** Run the prompts without the proposed guidance. Record the incorrect activation or behavior and the agent's rationalization.
4. **GREEN.** Add the smallest guidance that fixes the observed failure. Keep non-critical explanation outside `SKILL.md`.
5. **REFACTOR.** Re-run the cases, close only demonstrated loopholes, remove duplication, and route detailed material into references.
6. **Deploy safely.** Validate frontmatter, links, dependencies, examples, size, and behavioral cases before publishing.

## Progressive disclosure

Keep the active file focused on purpose, required workflow, safety gates, and routing. Put long examples, background, tool references, troubleshooting, and human-facing maintenance material under `references/`. Link each reference from the step where it becomes relevant; do not require loading every reference up front.

Target budgets:

| Type | Main-file target |
|---|---:|
| Startup/meta | under 200 words |
| Thin wrapper | under 100 words |
| Technique or pattern | under 500 words |
| Complex workflow | under 800 words |

## Required gates

- Directory and frontmatter `name` match.
- Automatic descriptions start with `Use when` and describe triggers, not steps.
- Manual wrappers state the explicit invocation and user-visible outcome.
- Dependencies, aliases, clients, tools, and commands are declared.
- Public guidance contains no private paths, hosts, accounts, or secrets.
- Relative links resolve and examples parse.
- Safety-sensitive commands include explicit constraints and regression cases.
- A failing evaluation was observed before the guidance change, then passed afterward.

## Load references when needed

- Description and discovery work: [description optimisation](references/description-optimisation.md)
- Evaluation design: [testing methodology](references/testing-methodology.md)
- Resistance and loopholes: [rationalisation patterns](references/rationalisation-patterns.md)
- Fast wording experiments: [micro-testing](references/micro-testing.md)
- Pre-publication checks: [deployment checklist](references/deployment-checklist.md)
- Complete historical guidance and examples: [full guidance](references/full-guidance.md)

## Stop conditions

Stop and return to RED when the change has no failing case, when an exception exists only to make validation green, or when the main file grows because optional reference material was copied into activation context.
