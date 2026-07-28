# Rationalisation patterns

When an evaluation fails, capture the agent’s stated reason. Convert repeated reasons into explicit gates only when they represent real loopholes.

| Rationalisation | Guidance response |
|---|---|
| “This change is too small” | State which safety or workflow gates apply regardless of size. |
| “The intent is obvious” | Require an observable test or evidence before the claim. |
| “Equivalent verification is enough” | Name the exact acceptable evidence and permitted substitutions. |
| “I’ll fix it after implementation” | State the required ordering and restart condition. |
| “The user probably meant…” | Define when clarification is mandatory. |

Avoid scolding language or an ever-growing prohibition list. Prefer one enforceable principle, a short red-flag list, and an explicit recovery action.

See [full guidance](full-guidance.md#common-rationalizations-for-skipping-testing) for extended examples.
