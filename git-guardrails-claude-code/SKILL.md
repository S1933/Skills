---
name: git-guardrails-claude-code
description: Use when setting up Claude Code hooks to prevent pushes or destructive Git operations from running without user control.
compatibility: Requires Claude Code with Bash PreToolUse hooks and Python 3.
---

# Setup Git Guardrails

Sets up a PreToolUse hook that intercepts and blocks dangerous git commands before Claude executes them.

## What Gets Blocked

- `git push` (all variants including `--force`)
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore .`

`git push --dry-run` and `git clean --dry-run` are allowed, including when
force flags are also present, because Git does not mutate state in dry-run
mode.

The hook recognises absolute Git paths, `command git`, `env ... git`, Git
global options such as `-C`, and commands after shell separators. Blocked and
invalid-input decisions exit with code `2` and emit one of these stable codes:

- `GIT_GUARDRAIL_BLOCKED`
- `GIT_GUARDRAIL_INPUT_ERROR`

When blocked, Claude sees a message telling it that it does not have authority to access these commands.

## Steps

### 1. Ask scope

Ask the user: install for **this project only** (`.claude/settings.json`) or **all projects** (`~/.claude/settings.json`)?

### 2. Copy the hook scripts

The bundled entry point and classifier are:

- [scripts/block-dangerous-git.sh](scripts/block-dangerous-git.sh)
- [scripts/classify-git-command.py](scripts/classify-git-command.py)

Copy both files into the target hook directory based on scope:

- **Project**: `.claude/hooks/`
- **Global**: `~/.claude/hooks/`

Make `block-dangerous-git.sh` executable. Python 3 is required; `jq` is not.

### 3. Add hook to settings

Add to the appropriate settings file:

**Project** (`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

**Global** (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-dangerous-git.sh"
          }
        ]
      }
    ]
  }
}
```

If the settings file already exists, merge the hook into existing `hooks.PreToolUse` array — don't overwrite other settings.

### 4. Ask about customization

Ask if user wants to add or remove any patterns from the blocked list. Edit the copied script accordingly.

### 5. Verify

Run the bundled fixture suite:

```bash
git-guardrails-claude-code/tests/test-guardrail.sh
```

It covers allowed commands, blocked commands, malformed input, absent command
fields, and an environment without `jq`.
