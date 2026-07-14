---
name: schema-validation
description: Use when defining or reviewing validation for configuration files, API payloads, manifests, serialized models, cross-field invariants, or human-readable validation errors.
---

# Schema Validation

## Overview

Validate at the boundary where untrusted data becomes a domain value. Separate decoding, structural checks, semantic invariants, and environmental checks so callers receive complete and actionable diagnostics.

## When to use

- Parsing YAML, JSON, TOML, form data, or API requests.
- Adding required fields, enums, regex constraints, references, or mutually exclusive fields.
- Deciding whether a missing external resource is an error or warning.
- Evolving a schema without silently breaking older documents.

## Validation layers

| Layer | Examples | Expected result |
|---|---|---|
| Decode | malformed YAML, wrong scalar type | Parse error with source context |
| Structure | missing required field, invalid enum | Field-path diagnostic |
| Semantics | XOR fields, duplicate IDs, unknown reference | Aggregated invariant errors |
| Environment | missing file, unavailable plugin | Error only when portability contract requires it; otherwise warning |

## Core pattern

1. Decode into an explicit schema type; reject or preserve unknown fields according to compatibility policy.
2. Accumulate independent validation failures instead of stopping at the first one.
3. Express locations as stable paths such as `agents[2].skills[0]`.
4. Validate cross-references after collecting all identifiers.
5. Keep pure validation free of filesystem, network, clock, and process-global state.
6. Perform environmental checks separately and classify their severity.

```go
func validateAgent(a Agent, path string) []string {
	var errs []string
	if a.ID == "" {
		errs = append(errs, path+".id is required")
	}
	for i, skill := range a.Skills {
		if !skillName.MatchString(skill) {
			errs = append(errs, fmt.Sprintf("%s.skills[%d] is invalid", path, i))
		}
	}
	return errs
}
```

## Quick reference

- Test valid minimum, valid maximum, zero value, malformed type, and every invariant.
- Test multiple simultaneous errors to prove aggregation.
- Keep error wording deterministic; sort diagnostics derived from maps.
- Treat validation success as permission to use the value, not merely successful decoding.
- Document compatibility behavior for new, removed, and unknown fields.

## Common mistakes

- Mixing defaulting with validation until invalid input becomes indistinguishable from omission.
- Checking filesystem existence in a shared schema when documents are intentionally portable.
- Returning generic messages such as `invalid config` without a field path.
- Validating only happy-path fixtures and assuming the decoder enforces domain rules.
