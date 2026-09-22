---
name: binary-distribution
description: Use when releasing compiled command-line tools across operating systems or architectures, including version metadata, archives, checksums, signing, installers, and reproducible release automation.
---

# Binary Distribution

## Overview

Treat release artifacts as a verifiable supply chain: build from an immutable revision, identify every artifact, publish integrity metadata, and test installation on clean target environments.

## When to use

- Shipping Go, Rust, or other compiled CLI binaries.
- Designing GitHub Release workflows and archive naming.
- Writing `curl | sh` installers or upgrade commands.
- Adding checksums, signatures, SBOMs, provenance, or release verification.

## Release contract

1. Build from a tag that resolves to the reviewed commit.
2. Produce an explicit OS/architecture matrix.
3. Embed version, commit, and build date through supported linker metadata.
4. Use stable artifact names: `<tool>_<version>_<os>_<arch>.<ext>`.
5. Archive the binary with license/readme only when useful to installation.
6. Publish SHA-256 checksums and, when required, signatures/provenance.
7. Installers download to a temporary location, verify, then atomically place the binary.
8. Smoke-test `--version` and one real command on every supported platform.

```sh
asset="tool_${version}_${os}_${arch}.tar.gz"
curl --fail --location --output "$tmp/$asset" "$release/$asset"
curl --fail --location --output "$tmp/checksums.txt" "$release/checksums.txt"
(cd "$tmp" && shasum -a 256 -c checksums.txt --ignore-missing)
```

## Quick reference

| Concern | Required evidence |
|---|---|
| Supported matrix | CI jobs for each declared target |
| Integrity | Published checksum verified before install |
| Traceability | `tool --version` reports tag and commit |
| Compatibility | Minimum OS/runtime assumptions documented |
| Repeatability | Release workflow runs from clean checkout |
| Rollback | Previous immutable release remains available |

## Installer rules

- Fail on HTTP errors and checksum mismatch.
- Detect OS/architecture explicitly; reject unknown combinations.
- Never execute downloaded content before verification.
- Avoid requiring root; support a user-owned destination.
- Print the installed path and PATH remediation when needed.

## Common mistakes

- Naming assets inconsistently with installer lookup rules.
- Publishing mutable `latest` artifacts without immutable versioned equivalents.
- Testing compilation but not the archived binary users download.
- Omitting checksum verification from the installer.
- Building locally and uploading files outside the audited release workflow.
