---
name: brainstorming
description: Use when creating features, components, functionality, or any behaviour change that requires intent and design to be clarified before implementation.
compatibility: Agent Skills compatible; the optional visual companion requires Node.js and a local browser.
---

# Brainstorming Ideas Into Designs

Turn an idea into an agreed design before implementation. Even apparently small changes can hide product, interface, or compatibility decisions.

## Process

1. Inspect relevant repository context: instructions, current behavior, nearby code, tests, docs, and recent changes.
2. Ask one focused question at a time. Clarify the user-visible outcome, constraints, non-goals, compatibility, failure behavior, and success criteria.
3. Offer two or three genuinely different approaches when a meaningful design choice exists. State tradeoffs and make a recommendation.
4. Present the design in short sections appropriate to its complexity: responsibilities, interfaces, data flow, state, errors, testing, rollout, and open risks.
5. Ask for confirmation after each material section. Revise disagreements before continuing.
6. Record the approved design in the project’s preferred documentation location, then hand off to `writing-plans` when implementation is requested.

## Guardrails

- Do not write implementation code, scaffold files, or install dependencies before design approval.
- Do not force unnecessary ceremony; a tiny change may need only a few explicit decisions.
- Do not ask several unrelated questions in one message.
- Do not silently choose behavior that changes public interfaces, data ownership, security, or migration requirements.
- Distinguish facts discovered in the repository from assumptions requiring user confirmation.

## Visual companion

Use the optional local visual companion only when comparing layouts, flows, or visual alternatives materially improves the decision. Read [visual-companion.md](visual-companion.md) before starting it. Text is the default.

The extended question catalogue, examples, and anti-pattern rationale are in [full guidance](references/full-guidance.md). The design reviewer prompt is [spec-document-reviewer-prompt.md](spec-document-reviewer-prompt.md).
