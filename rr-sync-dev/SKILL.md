---
name: rr-sync-dev
description: Use when syncing local project files to a configured development server through the rr Zsh function, or when rr produces unexpected results.
compatibility: Environment-specific; requires Zsh, Git, rsync, SSH, and local RR_* configuration.
---

# rr — rsync sync to remote development

One-way `rsync` push from a local working tree to a configured development
server.

- **Remote**: `$RR_REMOTE_HOST`
- **Destination**: `$RR_REMOTE_PROJECT_ROOT/<PROJECT>`
- **Default project**: `$RR_DEFAULT_PROJECT`

Set these values from the ignored `.local/skills-environment.yaml` inventory
before sourcing the function. Do not commit the resolved host or path.

## Usage

```zsh
# Explicit files or directories
rr chemin/vers/fichier.php autre/dossier/

# Select a project explicitly
rr --project tmgmt chemin/vers/fichier.php
rr -p tmgmt chemin/vers/fichier.php

# Preview without prompting or transferring
rr --dry-run chemin/vers/fichier.php

# No args: sync everything from git status
rr
```

## Behaviour

1. `-p` / `--project` selects a project; otherwise `$RR_DEFAULT_PROJECT` is used.
   Every positional argument is a file or directory.
2. **No file args** → file list built from NUL-delimited
   `git status --porcelain=v1 -z`, including safe handling of spaces, Unicode,
   copies and renames. The new path is used for renames.
3. File list is printed, then confirmation prompt `(y/N)` — only `y`/`Y` proceeds.
4. Each file is synced after shell-escaping the remote destination and using
   `--` before rsync operands:
   - **Directory** → contents synced (`trailing /` on source).
   - **File** → direct sync.
   - **Missing locally** → skipped with `⚠️ Missing:` (e.g. deleted files from git status — deletions are NOT propagated).
5. `--dry-run` prints the resolved project and files without prompting or
   invoking `rsync`.

## Pitfalls

- Explicit paths are resolved from the current directory, confined to the Git
  working tree, and mapped to repository-relative remote destinations.
- Sync is **one-way** (local → remote), no `--delete`. Deleted local files are NOT removed remotely.
- For bidirectional sync, use a dedicated bidirectional synchronisation tool.

## Installation

Sourced from `~/.zshrc`:

```zsh
source ~/.claude/skills/rr-sync-dev/rr.zsh
```

## Diagnostics

| Symptom | Likely cause |
|---------|-------------|
| `⚠️ Missing: …` | File listed by git status was deleted locally; sync does not propagate deletions |
| `ssh: Could not resolve hostname` | `$RR_REMOTE_HOST` is wrong or unavailable |
| `rsync: change_dir … failed` | Project directory does not exist under `$RR_REMOTE_PROJECT_ROOT` |
| `Git working tree required …` | `rr` was called without files outside a Git working tree |
