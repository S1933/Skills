---
name: scaleflex-api
description: Use when integrating the Scaleflex, Filerobot, or Cloudimage API — searching DAM assets by metadata, uploading files, running Visual AI models, or invalidating CDN cache.
---

# Scaleflex API

## Overview

Scaleflex ships three API families under one Postman-published reference at
`developers.scaleflex.com`. There is no OpenAPI spec, no sitemap, and no
indexable page URLs — the published collection JSON is the only
machine-readable source. Product guides live separately at
`docs.scaleflex.com`, which does expose `llms.txt` and serves any page as
Markdown by appending `.md`.

The three families use **different hosts and different auth**. Confusing them
is the most common integration failure.

| Family | Host | Auth |
|---|---|---|
| DAM (Filerobot) | `api.filerobot.com/<token>/v5/…` | `<token>` in path + `X-Filerobot-Key: <api-key>` |
| Visual AI | `ai.scaleflex.com/…` | `Filerobot-Token` + `Filerobot-Key` headers |
| Cloudimage (DMO) | `api.cloudimage.com` | `X-Client-Key` |

Header casing is inconsistent across the published examples
(`X-Filerobot-Key`, `Filerobot-Key`, `x-filerobot-key`); treat it as
case-insensitive. Visual AI keys need the `FILE_UPLOAD` permission.

## Search is where the leverage is

`GET /<token>/v5/files?q=…` is the endpoint that matters. Its grammar filters
structured metadata precisely:

```
q=asset_type:"Illustration"+topic:Sovereignty   # + is AND
q=product:BareMetal,PublicCloud                 # , is OR
q=product:-legacy                               # - is NOT
q=credit:empty        q=credit:non-empty        # presence
q="rights expiry">2026-07-29                    # dates; .. for ranges
```

**The trap:** TEXT and TEXTAREA fields support only `~` with exact matching.
Titles, descriptions, and alt text are therefore weak retrieval signals.
Design retrieval around SELECT/MULTI_SELECT fields, or accept the untargeted
fuzzy form `q="some phrase"`.

Native filters that are easy to miss: `orientation`, `resolution`, `type`,
`mimetype`, `size`, `labels` — plus `faces` and `color` once the matching AI
post-process is enabled on the project.

Full grammar: [references/search-grammar.md](references/search-grammar.md).

## Reserved keywords

These cannot be used as custom metadata field keys:

`type` · `orientation` · `mimetype` · `color` · `resolution` · `faces` ·
`approval_status` · `enable_favorited`

Verify a planned taxonomy against this list first. Renaming a field later
means a bulk re-tag of the whole library.

## Gotchas

- **Filename-based URLs are not stable.** `https://<token>.filerobot.com/<path>`
  breaks when an asset is renamed or re-versioned. Prefer the UUID route
  `GET /v5/get/<file_uuid>`, or persist the `permalink` returned at upload.
  This bites hardest on static sites, where URLs are baked at build time.
- **Version prefixes differ**: DAM is `v5`, Video `v2`, one Airbox endpoint `v4`.
- **Portals and Shareboxes have no API** — they are Hub-only features.
- **Upload carries no metadata.** Apply it with a follow-up
  `PATCH /<token>/v5/file/<uuid>/meta`.

## Reference material

- [references/endpoints.md](references/endpoints.md) — endpoint map, all three families
- [references/upload-and-delivery.md](references/upload-and-delivery.md) — multipart upload, response URL shapes, CDN transforms
