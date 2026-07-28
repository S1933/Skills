# Skill authoring standard

## Discovery metadata

Descriptions are activation metadata, not workflow summaries. They answer one
question: “Should an agent load this skill for the current request?”

### Automatically invoked skills

Use this form:

```yaml
description: Use when <observable trigger conditions>.
```

Requirements:

- start with `Use when`;
- describe concrete task types, symptoms, or uncertainty;
- remain in third person and avoid client-specific process steps;
- target 80–250 characters, with a hard maximum of 500;
- keep comparisons and implementation sequences in the skill body.

Good:

```yaml
description: Use when tests fail intermittently, depend on timing, or expose a race condition.
```

Bad:

```yaml
description: Debugs tests by reproducing, tracing logs, writing a patch, and rerunning the suite.
```

The bad version both lacks a trigger and lets an agent imitate a shortened
workflow without loading the skill.

### Manually invoked skills

Use this form:

```yaml
description: Use when explicitly invoking /<skill-name> to <user-visible outcome>.
```

Manual wrappers may omit the literal slash command only when another runtime
mechanism is the documented entry point. That exception must appear in
`validation-exceptions.yaml` with a reason and removal phase.

## Frontmatter

- `name` and `description` are required.
- `name` must match its directory and use lowercase letters, digits, and
  hyphens.
- `disable-model-invocation`, when present, must be a boolean.
- `compatibility` is required whenever the skill depends on a particular
  client, hook system, local command, issue tracker, browser, or subagent API.
- Keep frontmatter at or below 1,024 bytes.

## Compatibility classifications

Use one or more of these classifications in `skills-manifest.yaml`:

- `agent-skills`: portable skill with no client-specific runtime requirement;
- `claude-code`: requires Claude Code tools, hooks, or command semantics;
- `codex`: requires Codex CLI or Codex runtime behaviour;
- `opencode`: requires OpenCode-specific behaviour;
- `local-shell`: requires locally configured commands or infrastructure.

Portable skills should describe capabilities rather than naming one client's
tool names. Non-portable skills must state their assumptions in `compatibility`
and declare commands, tools, or client features in the manifest.

## Content and size

- Resolve every relative Markdown link.
- Declare supporting files and cross-skill references in the manifest.
- Do not publish unresolved `TBD` or `TODO` placeholders.
- Put heavy references in supporting files and link them from `SKILL.md`.
- Treat 1,200 words in a main skill as a migration warning until the progressive
  disclosure phase is complete.
