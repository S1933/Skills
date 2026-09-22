---
name: adapter-pattern
description: Use when one domain model must interoperate with multiple external APIs, file formats, providers, CLIs, storage engines, or versioned protocols without leaking vendor details into core logic.
---

# Adapter Pattern

## Overview

Keep the domain vocabulary stable while adapters translate at system boundaries. The core owns intent; each adapter owns target-specific representation and lossiness.

## When to use

- Supporting multiple providers behind one use case.
- Translating a canonical model into native configuration formats.
- Isolating vendor SDK types, protocol versions, or filesystem layouts.
- Testing merge, mapping, or degradation behavior independently of orchestration.

Do not introduce an interface merely to wrap one concrete type with no alternate implementation, test seam, or boundary policy.

## Core pattern

1. Define the port in terms of domain inputs and outcomes.
2. Place target-specific validation and mapping inside the adapter.
3. Keep orchestration responsible for sequencing and I/O policy, not field translation.
4. Make lossy mappings explicit and test them.
5. Preserve unknown native data when the adapter updates only a managed subset.
6. Use capability interfaces only for genuinely optional behavior.

```go
type Adapter interface {
	Name() string
	GenerateAgent(AgentDefinition) (map[string]string, error)
}

type Merger interface {
	MergeFile(path string, existing []byte, fragments map[string]any) ([]byte, error)
}
```

The small base interface keeps every target implementable. Orchestration checks `Merger` only for formats that require partial native-file ownership.

## Quick reference

| Decision | Owner |
|---|---|
| Canonical meaning | Domain/core |
| Native field names and layout | Adapter |
| Target-specific validation | Adapter |
| File discovery and atomic writes | Orchestration/infrastructure |
| Merge preservation policy | Explicit adapter capability |
| Unsupported domain feature | Documented degradation or error |

## Testing

- Contract tests: every adapter satisfies shared invariants.
- Mapping tests: each domain field reaches the correct native field.
- Golden tests: complete native artifacts remain stable.
- Preservation tests: unmanaged native fields survive merges.
- Absence tests: optional zero values do not create unwanted output.

## Common mistakes

- Returning vendor SDK objects from the domain interface.
- Building a universal interface containing every provider capability.
- Scattering `if provider == ...` branches through core logic.
- Replacing an entire user-owned file when only one nested block is managed.
- Hiding lossy translation behind silent defaults.
