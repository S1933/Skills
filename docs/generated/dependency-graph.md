<!-- Generated from skills-manifest.yaml; do not edit manually. -->

# Skill dependency graph

Solid edges are required installation dependencies. Dashed edges are optional workflow integrations. Informational references are omitted.

```mermaid
flowchart LR
  brainstorming["brainstorming"]
  codebase_design["codebase-design"]
  codex["codex"]
  decision_mapping["decision-mapping"]
  domain_modeling["domain-modeling"]
  executing_plans["executing-plans"]
  finishing_a_development_branch["finishing-a-development-branch"]
  grill_me["grill-me"]
  grill_with_docs["grill-with-docs"]
  grilling["grilling"]
  implement["implement"]
  improve["improve"]
  improve_codebase_architecture["improve-codebase-architecture"]
  prototype["prototype"]
  repository_reconnaissance["repository-reconnaissance"]
  requesting_code_review["requesting-code-review"]
  subagent_driven_development["subagent-driven-development"]
  systematic_debugging["systematic-debugging"]
  tech_debt_audit["tech-debt-audit"]
  test_driven_development["test-driven-development"]
  to_issues["to-issues"]
  to_prd["to-prd"]
  triage["triage"]
  using_git_worktrees["using-git-worktrees"]
  using_superpowers["using-superpowers"]
  verification_before_completion["verification-before-completion"]
  writing_plans["writing-plans"]
  writing_skills["writing-skills"]
  decision_mapping -. optional .-> domain_modeling
  decision_mapping -. optional .-> grilling
  decision_mapping -. optional .-> prototype
  decision_mapping -. optional .-> to_prd
  executing_plans -->|requires| finishing_a_development_branch
  executing_plans -->|requires| using_git_worktrees
  executing_plans -. optional .-> subagent_driven_development
  executing_plans -. optional .-> writing_plans
  grill_me -->|requires| grilling
  grill_with_docs -->|requires| domain_modeling
  grill_with_docs -->|requires| grilling
  implement -->|requires| requesting_code_review
  implement -->|requires| test_driven_development
  implement -->|requires| verification_before_completion
  improve -->|requires| repository_reconnaissance
  improve_codebase_architecture -->|requires| codebase_design
  improve_codebase_architecture -->|requires| grilling
  improve_codebase_architecture -->|requires| repository_reconnaissance
  improve_codebase_architecture -. optional .-> domain_modeling
  subagent_driven_development -->|requires| finishing_a_development_branch
  subagent_driven_development -->|requires| requesting_code_review
  subagent_driven_development -->|requires| test_driven_development
  subagent_driven_development -->|requires| using_git_worktrees
  subagent_driven_development -. optional .-> executing_plans
  subagent_driven_development -. optional .-> implement
  subagent_driven_development -. optional .-> writing_plans
  systematic_debugging -->|requires| test_driven_development
  systematic_debugging -. optional .-> verification_before_completion
  tech_debt_audit -->|requires| repository_reconnaissance
  to_issues -. optional .-> triage
  to_prd -. optional .-> triage
  triage -. optional .-> domain_modeling
  triage -. optional .-> grilling
  using_superpowers -. optional .-> brainstorming
  using_superpowers -. optional .-> codex
  using_superpowers -. optional .-> systematic_debugging
  writing_plans -. optional .-> executing_plans
  writing_plans -. optional .-> subagent_driven_development
  writing_plans -. optional .-> using_git_worktrees
  writing_skills -->|requires| test_driven_development
  writing_skills -. optional .-> systematic_debugging
```

## Declared dependencies

| Skill | Required | Optional |
|---|---|---|
| adapter-pattern | — | — |
| atomic-file-write | — | — |
| binary-distribution | — | — |
| brainstorming | — | — |
| caveman | — | — |
| [REMOVED-INTERNAL-SKILL] | — | — |
| codebase-design | — | — |
| codex | — | — |
| decision-mapping | — | `domain-modeling`, `grilling`, `prototype`, `to-prd` |
| design-an-interface | — | — |
| dispatching-parallel-agents | — | — |
| domain-modeling | — | — |
| embedded-fixtures | — | — |
| executing-plans | `finishing-a-development-branch`, `using-git-worktrees` | `subagent-driven-development`, `writing-plans` |
| finishing-a-development-branch | — | — |
| git-guardrails-claude-code | — | — |
| go-cli-conventions | — | — |
| golden-file-testing | — | — |
| grill-me | `grilling` | — |
| grill-with-docs | `domain-modeling`, `grilling` | — |
| grilling | — | — |
| handoff | — | — |
| implement | `requesting-code-review`, `test-driven-development`, `verification-before-completion` | — |
| improve | `repository-reconnaissance` | — |
| improve-codebase-architecture | `codebase-design`, `grilling`, `repository-reconnaissance` | `domain-modeling` |
| [REMOVED-INTERNAL-SKILL] | — | — |
| migrate-to-shoehorn | — | — |
| [REMOVED-INTERNAL-SKILL] | — | — |
| prototype | — | — |
| qa | — | — |
| receiving-code-review | — | — |
| repository-reconnaissance | — | — |
| request-refactor-plan | — | — |
| requesting-code-review | — | — |
| resolving-merge-conflicts | — | — |
| review-scope | — | — |
| [REMOVED-INTERNAL-SKILL] | — | — |
| [REMOVED-INTERNAL-SKILL] | — | — |
| schema-validation | — | — |
| setup-pre-commit | — | — |
| subagent-driven-development | `finishing-a-development-branch`, `requesting-code-review`, `test-driven-development`, `using-git-worktrees` | `executing-plans`, `implement`, `writing-plans` |
| systematic-debugging | `test-driven-development` | `verification-before-completion` |
| tech-debt-audit | `repository-reconnaissance` | — |
| test-driven-development | — | — |
| to-issues | — | `triage` |
| to-prd | — | `triage` |
| triage | — | `domain-modeling`, `grilling` |
| ubiquitous-language | — | — |
| using-git-worktrees | — | — |
| using-superpowers | — | `brainstorming`, `codex`, `systematic-debugging` |
| verification-before-completion | — | — |
| writing-plans | — | `executing-plans`, `subagent-driven-development`, `using-git-worktrees` |
| writing-skills | `test-driven-development` | `systematic-debugging` |
