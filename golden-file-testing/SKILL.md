---
name: golden-file-testing
description: Use when testing generated text, configuration, serialization, templates, compiler output, or other stable artifacts whose complete shape matters more than isolated fields.
---

# Golden File Testing

## Overview

Golden tests compare a complete produced artifact with a reviewed file checked into source control. Make updates explicit and review the golden diff as carefully as production code.

## When to use

- Output has many meaningful fields or formatting rules.
- A renderer or adapter must remain byte-stable.
- A full artifact communicates intent better than dozens of assertions.
- Regression risk includes omitted, reordered, or unexpectedly added content.

Do not use a golden file for volatile timestamps, random IDs, huge opaque blobs, or behavior better expressed as a small semantic assertion.

## Core pattern

1. Produce output using the real public boundary.
2. Normalize only intentionally irrelevant variation.
3. Compare against `testdata/<case>.golden`.
4. Fail with a readable diff, not only `got != want`.
5. Gate regeneration behind an explicit flag such as `-update` or `WRITE_GOLDEN=1`.
6. After regeneration, inspect and explain every changed line.

```go
var update = flag.Bool("update", false, "update golden files")

func assertGolden(t *testing.T, path string, got []byte) {
	t.Helper()
	if *update {
		if err := os.WriteFile(path, got, 0o644); err != nil { t.Fatal(err) }
	}
	want, err := os.ReadFile(path)
	if err != nil { t.Fatal(err) }
	if diff := cmp.Diff(string(want), string(got)); diff != "" {
		t.Fatalf("golden mismatch (-want +got):\n%s", diff)
	}
}
```

## Quick reference

| Output | Comparison policy |
|---|---|
| User-facing text | Byte-for-byte, including final newline |
| JSON semantics | Decode and compare values when key order is irrelevant |
| JSON formatting | Byte-for-byte when indentation/order is contractual |
| Paths | Replace test temp roots with a stable placeholder |
| Maps | Sort before rendering; never normalize accidental nondeterminism away |

## Common mistakes

- Automatically updating goldens in normal test runs: failures become silent approvals.
- Regenerating before observing the expected failure: the test never proves sensitivity.
- Normalizing fields that users actually see or depend on.
- Storing enormous fixtures that reviewers cannot meaningfully audit.
- Asserting the same shape both field-by-field and with a golden without a distinct reason.
