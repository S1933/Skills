---
name: test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code
---

# Test-Driven Development

Drive each behavior change through RED, GREEN, and REFACTOR.

## Iron law

Do not write or retain production code for new behavior before observing a relevant test fail for the expected reason. If implementation came first, remove it and restart from the test.

## Cycle

### RED

Write one small test for one observable behavior. Name it in domain language, exercise the real public boundary, and avoid mocks unless the boundary genuinely requires a test double.

Run the narrowest command that executes the test. Confirm it fails because the behavior is absent—not because of syntax, setup, imports, or a mistaken assertion. A test that passes immediately does not establish RED; correct the test or choose missing behavior.

### GREEN

Write the minimum production code that makes the failing test pass. Do not add speculative abstractions, unrelated cleanup, extra options, or behavior not demanded by a failing test.

Run the same test and inspect the output. Then run the relevant surrounding suite to detect regressions.

### REFACTOR

With tests green, improve names, duplication, boundaries, and clarity without changing behavior. Keep tests green after each refactor. Then select the next behavior and return to RED.

## Good tests

- Demonstrate user-visible or caller-visible behavior.
- Fail clearly when that behavior breaks.
- Use realistic inputs and the smallest useful scope.
- Avoid asserting implementation details, mock call choreography, or test-only production hooks.
- Cover error behavior and boundaries as separate cycles when material.

## Existing code and bug fixes

For a bug, first reproduce it with a regression test. For difficult legacy seams, add a characterization test or create the smallest safe seam, then continue the cycle. Do not use “the code already exists” to skip observing RED for the new behavior.

## Completion gate

Before claiming done, verify each new behavior had an observed RED, all relevant tests pass now, output has no unexpected warnings, and no test was weakened merely to obtain GREEN.

Read [testing anti-patterns](testing-anti-patterns.md) when mocks, fixtures, helpers, or test-only APIs are becoming complex. Extended examples and rationalization handling are in [full guidance](references/full-guidance.md).
