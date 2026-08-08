---
name: review-scope
description: Use when beginning a code review that must include committed, staged, unstaged, and relevant untracked changes against the correct base.
compatibility: Requires Git repository access.
---

# Review Scope

Establish exactly what to review before forming any judgment. Skipping this means reviewing a partial diff and missing regressions.

## 1. Determine the base branch

Resolve the base in preference order — stop at the first that yields a
definitive result:

1. **Explicit user-provided base** — highest priority; never guess over it.
2. **Pull/merge request base** — if the current branch has an open PR/MR,
   use its declared target (e.g. `gh pr view --json baseRefName -q .baseRefName`
   or the MR equivalent / the `origin/<target>` ref).
3. **Remote default branch** — `git symbolic-ref refs/remotes/origin/HEAD`
   (usually `origin/main`).
4. **Best-guess fallback, confirmed with the user** — e.g. the repository
   default visible from `origin/HEAD`; if still ambiguous, ask before reviewing.

After selecting the base, run a separate unpushed-commits check — this is
not a base-selection step and must not gate the review. Only run this when
a tracking branch exists (skip on detached HEAD or branches without an
upstream):

```
git rev-parse --abbrev-ref @{upstream} >/dev/null 2>&1 \
  && git rev-list @{upstream}..HEAD --count \
  || echo "no upstream configured — skipping unpushed check"
```

If the count is non-zero, warn the reviewer that commits have not been pushed;
the review should still proceed against the selected base.

Legacy heuristic (first existing of `develop` → `origin/develop` → `main` →
`origin/main`) should only be used as the final fallback, and only after
checking for an explicit base and a PR base. Prefer the
remote (`origin/main`, `origin/develop`) over a possibly stale local branch so an
obsolete local `develop` is not mistaken for the real base.

Use `git show-ref --verify` to check each candidate and stop at the first that
exists.

## 2. Inspect every layer of change

Run all of these — each surfaces a different slice of the work:

- `git status --short`
- `git diff --name-status`
- `git diff`
- `git diff --cached`
- `git diff <base>...HEAD`
- `git diff <base>...HEAD --stat`

## 3. Review all current work

Cover committed branch changes, staged changes, unstaged changes, and relevant untracked files when they appear in `git status`. A change is in scope regardless of which layer it lives in.
