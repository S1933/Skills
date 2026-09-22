# Endpoint map

Derived from the Postman collection published at `developers.scaleflex.com`
(~176 requests across ~72 folders). The collection is the authoritative
source; this map exists so you can find the right family fast without
re-crawling the SPA.

The reference site is a JavaScript app with no sitemap, no `llms.txt`, and no
per-endpoint URLs — fetching it as HTML returns only a title. To read it
programmatically, fetch the underlying Postman collection JSON rather than the
page. Conceptual product guides are at `docs.scaleflex.com`, which does expose
`llms.txt` and serves any page as Markdown by appending `.md`.

## 1. DAM — Filerobot

Base: `https://api.filerobot.com/<token>/v5`
Auth: `<token>` in the path **and** `X-Filerobot-Key: <api-key>`.

| Area | Representative endpoints |
|---|---|
| Files | `GET /files` (search), `GET /get/<uuid>`, `PATCH /file/<uuid>`, `DELETE /file/<uuid>` |
| Upload | `POST /files?folder=/<path>` (multipart), remote-URL ingest |
| Metadata | `GET /meta` (field definitions), `PATCH /file/<uuid>/meta` |
| Folders | `GET /folders`, create / rename / move / delete |
| Versions | list, restore, delete a file version |
| Tags & labels | list, attach, detach |
| Users, teams, roles | CRUD, permission assignment |
| Approvals | approval status transitions on an asset |
| Trash | list, restore, purge |
| Search presets | saved queries |

Notable: **Portals and Shareboxes have no API** — they are Hub-only features.
Anything you need to automate around distribution must be built on search plus
delivery URLs.

## 2. Video

Base: `https://api.filerobot.com/videos/v2`

Separate version prefix from the rest of the DAM. Covers upload, encoding
profiles, playback URLs, and thumbnails. Same key material as the DAM.

## 3. Visual AI

Base: `https://ai.scaleflex.com`
Auth: `Filerobot-Token` **and** `Filerobot-Key` headers (note: no `X-` prefix
here). The key must carry the `FILE_UPLOAD` permission, even for endpoints
that only read.

Model families: image tagging / labelling, object and face detection,
background removal, upscaling, cropping suggestions, NSFW and quality scoring,
caption and alt-text generation.

Two calling styles appear in the collection: submit an image by URL, or upload
bytes directly. Some models are asynchronous — they return a job handle you
poll rather than a result.

## 4. Cloudimage / DMO

Base: `https://api.cloudimage.com`
Auth: `X-Client-Key`.

Administrative API for the CDN: cache invalidation (per-URL and per-prefix),
usage and bandwidth statistics, origin configuration, and token settings.
Image transformation itself is not done here — it happens on the delivery
domain via query parameters (see `upload-and-delivery.md`).

## 5. Airbox

One endpoint in the collection uses a `v4` prefix. Treat version prefixes as
per-family, never global.

## Known defects in the published reference

- **Header casing is inconsistent** across examples: `X-Filerobot-Key`,
  `Filerobot-Key`, `x-filerobot-key`. Servers accept any casing; the docs are
  simply not normalised.
- **Three endpoints marked `[RE]` have a malformed `https://https://` prefix**
  in their example URL. Strip the duplicate scheme.
- **Version prefixes are mixed** (`v5` DAM, `v2` Video, `v4` Airbox). Copying a
  path between families without adjusting the version yields a 404.
- Some examples embed a literal project token in the URL. Replace it with your
  own; do not assume the sample token is a shared sandbox.
