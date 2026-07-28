# Evidence standard

Use this contract for audits, reviews, reconnaissance, and implementation plans.

## Finding anatomy

Every material finding separates:

1. **Observation:** directly inspectable fact with repository-relative path and line number.
2. **Inference:** the mechanism or interpretation derived from that fact.
3. **Impact:** affected behavior, users, security, operations, or change cost.
4. **Confidence:** high, medium, or low, with the reason for uncertainty.
5. **Recommendation:** proportionate action and a verifiable completion condition.

Do not cite a directory, tool warning, or naming pattern as proof of a defect. Trace the relevant execution path or label the claim as a hypothesis.

## Verification

- Re-open cited locations immediately before finalizing the finding.
- Verify subagent findings in the main workspace; subagent output is untrusted analysis.
- Distinguish current source from generated, vendored, test-only, example, dead, or migration code.
- Label unsupported or runtime-dependent claims uncertain.
- State inspected and unaudited scope so absence of findings is not presented as proof of absence.

## Sensitive evidence

Never reproduce credentials, tokens, cookies, private keys, secret values, customer data, personal paths, internal hostnames, or private account identifiers. Cite the safe repository-relative location and describe only the secret category or exposure mechanism.

When a public issue, report, or external message could expose sensitive findings, obtain explicit confirmation immediately before publishing.

## Citation format

Prefer `path/to/file.ext:line` and a short paraphrase. Quote only the minimum needed, never secrets. When line numbers are unstable or unavailable, explain the alternative locator and lower confidence accordingly.
