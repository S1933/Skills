---
name: atomic-file-write
description: Use when replacing configuration, state, generated, or user-owned files where crashes, partial writes, permissions, concurrent readers, or durability can corrupt observable state.
---

# Atomic File Write

## Overview

Publish a complete file in one rename operation. A temporary file must live in the destination directory so the final rename stays on the same filesystem.

## When to use

- Rewriting config, manifests, lockfiles, state files, or generated output.
- Protecting readers from truncated or half-serialized content.
- Preserving permissions while replacing an existing file.
- Requiring durability across process or machine failure.

## Core pattern

1. Serialize and validate content before touching the destination.
2. Create a uniquely named temporary file beside the destination.
3. Apply the intended mode and ownership policy.
4. Write all bytes, check close errors, and optionally `Sync` the file.
5. Rename the temporary path over the destination.
6. For crash durability, `Sync` the containing directory after rename.
7. Remove the temporary file on every pre-rename failure.

```go
func WriteFile(path string, data []byte, mode fs.FileMode) (err error) {
	dir := filepath.Dir(path)
	tmp, err := os.CreateTemp(dir, "."+filepath.Base(path)+"-*")
	if err != nil { return err }
	tmpPath := tmp.Name()
	defer func() {
		_ = tmp.Close()
		if err != nil { _ = os.Remove(tmpPath) }
	}()
	if err = tmp.Chmod(mode); err != nil { return err }
	if _, err = tmp.Write(data); err != nil { return err }
	if err = tmp.Sync(); err != nil { return err }
	if err = tmp.Close(); err != nil { return err }
	return os.Rename(tmpPath, path)
}
```

## Quick reference

| Requirement | Action |
|---|---|
| Reader atomicity | Temp file in destination directory + rename |
| File durability | Sync temp file before rename |
| Rename durability | Sync parent directory after rename |
| Existing mode | Stat destination and deliberately preserve or replace it |
| Windows support | Verify replacement semantics; rename-over-existing differs |
| Symlink safety | Decide whether replacing the link or its target is intended |

## Common mistakes

- Creating the temp file in `/tmp`: cross-device rename is not atomic and may fail.
- Deferring `Close` without checking its error: buffered write failures can be lost.
- Assuming rename protects against two writers: atomic publication is not mutual exclusion.
- Replacing permissions accidentally: define the mode policy explicitly.
- Calling a write atomic while omitting directory sync when crash durability is required.
