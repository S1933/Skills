# Testing methodology

Test both activation and compliance.

- Trigger cases: positive, negative, ambiguous, and collision prompts.
- Behavior cases: required actions, forbidden actions, ordering constraints, evidence requirements, and safety confirmations.
- Baseline: run without the proposed change and record the actual failure.
- Regression: run with the change repeatedly enough to detect unstable behavior.
- Review: inspect outputs for loopholes that aggregate metrics can hide.

Discipline skills need pressure scenarios that tempt shortcuts. Technique skills need application tasks. Reference skills need retrieval cases. Pattern skills need recognition and counterexamples.

For the complete subagent-based method, read [testing skills with subagents](../testing-skills-with-subagents.md). Historical examples are in [full guidance](full-guidance.md#testing-all-skill-types).
