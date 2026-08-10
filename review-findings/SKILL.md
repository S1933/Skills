---
name: review-findings
description: Use when reporting code-review findings, to keep severity and report shape identical across reviewers.
---

# Review Findings

One severity scale, one report shape. A synthesiser comparing several reviewers can
only merge findings that speak the same language.

## Severity — these four words, nothing else

- **critical** — data loss, security hole, or breakage on the main path. Blocks.
- **high** — wrong behaviour on a plausible path, or a contract silently broken. Blocks.
- **medium** — real defect on an unlikely path, or a cost the next reader pays. Does not block.
- **low** — worth knowing, safe to ship without. Does not block.

Never invent a fifth word: no "Important", no "nit", no "blocker". `critical` and
`high` block; `medium` and `low` do not.

## Every finding carries

- severity (one of the four)
- `file_path:line`, or the area when it is not one line
- what is wrong, in one sentence
- why it matters — the consequence, not a restatement
- suggested direction or fix

## Every report ends with

- **Verdict**: accepted | needs revision | rejected — justified by the worst
  surviving finding. A single unrefuted `critical` or `high` means at least
  `needs revision`.
- **Confidence**: 0-100% in your own findings, with one line of why.

These two lines, and the base you reviewed against, are **mandatory** and survive any
style or compression skill loaded alongside this one: a terse report still names its
base, its verdict and its confidence. Compress the prose, never the contract.

Findings only; do not edit files. If nothing in your remit is wrong, say so plainly —
an empty report is a result, not a failure.
