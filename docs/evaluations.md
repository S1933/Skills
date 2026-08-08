# Behavioural evaluations

Each automatically invoked skill owns `evals/<skill>/trigger.yaml` with at least five positive and five negative prompts. Suites include `ambiguous` and `collision` tags. Core workflow and safety skills also own `behaviour.yaml` cases with required and forbidden behavior.

The trigger suite copies the current manifest description; CI rejects stale copies so every description change requires reviewing its activation cases. `scripts/bootstrap-evals.py` creates a baseline for newly added automatic skills, but generated prompts must be reviewed for domain realism before merge.

Run structural coverage checks with:

```bash
python3 scripts/validate-evals.py
```

Client-specific runners execute the prompts and record observations without changing the fixture format. Store a run outside the repository or in an intentionally versioned results file:

```yaml
observations:
  - skill: systematic-debugging
    case: failing integration test
    expected_trigger: true
    triggered: true
    compliant: true
    collision: false
    context_tokens: 420
    run_group: debugging-repeat-1
```

Score an observed run with `python3 scripts/score-evals.py <results.yaml>`. It reports trigger precision/recall, compliance, collision rate, average context tokens, and repeated-run stability. Catalogue CI validates fixture coverage; model-facing runners remain client adapters so this repository does not hardcode one model or API.

# Bootstrap safety

Create only missing suites with `python3 scripts/bootstrap-evals.py
--all-missing`, or target one skill with `--skill <name>`. Existing files are
never replaced unless `--force` is supplied explicitly. The command reports
every created, skipped, or replaced file.
