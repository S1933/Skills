---
name: embedded-fixtures
description: Use when binaries or tests need deterministic templates, schemas, migrations, defaults, or sample files packaged with the executable through Go embed or an equivalent resource mechanism.
---

# Embedded Fixtures

## Overview

Embed immutable assets that are part of the program version. Keep user state and environment-specific configuration external.

## When to use

- Shipping default templates, schemas, migrations, or help examples.
- Making tests independent of the current working directory.
- Building a single distributable binary without runtime asset lookup.
- Versioning fixtures in lockstep with code that consumes them.

Do not embed secrets, mutable user data, large replaceable media, or configuration expected to change after compilation.

## Core pattern

1. Place assets in a dedicated package-owned directory.
2. Embed the narrowest stable glob; avoid accidentally including editor files or secrets.
3. Expose semantic functions instead of the raw filesystem when consumers need only named assets.
4. Return copies when callers may mutate byte slices.
5. Validate embedded content in tests using the same parser as production.
6. Document whether missing names are programmer errors or ordinary lookup failures.

```go
package fixtures

import (
	"embed"
	"fmt"
)

//go:embed defaults/*.yaml
var files embed.FS

func Default(name string) ([]byte, error) {
	b, err := files.ReadFile("defaults/" + name + ".yaml")
	if err != nil {
		return nil, fmt.Errorf("read embedded default %q: %w", name, err)
	}
	return b, nil
}
```

## Quick reference

| Need | Choice |
|---|---|
| Read-only asset tree | `embed.FS` |
| One text asset | embedded `string` |
| One binary asset | embedded `[]byte` |
| Editable installed default | Embed, then copy on explicit init |
| Test fixture only | Prefer `testdata/`; embed only if runtime packaging matters |

## Common mistakes

- Assuming embedded paths use host separators: they always use slash-separated paths.
- Embedding an overly broad directory containing credentials or large artifacts.
- Treating embedded defaults as writable state.
- Testing only asset presence instead of parsing and exercising the content.
- Hiding a large public API behind direct global `embed.FS` access.
