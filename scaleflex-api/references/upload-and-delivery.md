# Upload and delivery

## Uploading

```
POST https://api.filerobot.com/<token>/v5/files?folder=/<path>
X-Filerobot-Key: <api-key>
Content-Type: multipart/form-data
```

Send the bytes as a multipart part. The `folder` query parameter targets an
existing folder; creating the folder is a separate call. A remote-URL ingest
form also exists, where you pass a source URL instead of bytes — useful for
migrating an existing public library without downloading it first.

Minimal Node example:

```js
const form = new FormData();
form.append('file', new Blob([bytes], { type: mime }), filename);

const res = await fetch(
  `https://api.filerobot.com/${token}/v5/files?folder=${encodeURIComponent(folder)}`,
  { method: 'POST', headers: { 'X-Filerobot-Key': apiKey }, body: form },
);
const { files: [file] } = await res.json();
```

**Upload carries no metadata.** Custom fields are applied afterwards:

```
PATCH https://api.filerobot.com/<token>/v5/file/<uuid>/meta
```

So a complete ingest is always at least two calls per asset. Batch accordingly
and cap concurrency — four or five parallel uploads is a reasonable default.

Uploads are **not idempotent**. Re-running an ingest script creates duplicates
unless you first search for an existing asset (by filename or by a custom
`source_path` field you control) and skip or update it.

## What the response gives you

The uploaded-file object carries several ways to address the same asset. They
are not equivalent:

| Form | Shape | Stability |
|---|---|---|
| UUID | `<file_uuid>` | **Stable.** Survives rename, move, and re-version. |
| Permalink | absolute URL returned at upload | Stable; the safest thing to persist. |
| CDN path | `https://<token>.filerobot.com/<folder>/<filename>` | **Breaks on rename, move, or re-version.** |
| Public/origin URL | direct object URL | Implementation detail; do not persist. |

Persist the UUID (and optionally the permalink). Resolve to a delivery URL at
read time via `GET /<token>/v5/get/<file_uuid>`.

This matters most for static site generators, where URLs are baked into HTML
at build time: a filename-keyed URL that works at build will 404 the first
time someone renames the asset in the Hub, with no build to catch it. Keeping
a build-time manifest that maps your own local paths to UUIDs lets you
re-resolve on every build without touching content files.

## Delivery

`https://<token>.filerobot.com/<path>` serves DAM-hosted assets directly. No
separately configured origin is required — the DAM *is* the origin.

Cloudimage's proxy form is different: `https://<token>.cloudimg.io/<origin-url>`
fetches from a public origin you configure. Use it for assets that live outside
the DAM. It cannot reach a `localhost` origin, so local development against it
needs a tunnel or a fallback path.

## Transformations

Cloudimage transformation parameters are query-string based:

| Param | Meaning |
|---|---|
| `w`, `h` | target width / height in px |
| `q` | quality, 1–100 |
| `f=auto` | negotiate format (WebP/AVIF) from the `Accept` header |
| `func` | `crop`, `fit`, `bound`, `cover` |
| `gravity` | crop anchor, e.g. `auto`, `north`, `face` |
| `blur`, `sharp`, `greyscale` | filters |

```
https://<token>.filerobot.com/labs/hero.png?w=1200&q=80&f=auto&func=cover
```

> **Unverified.** Whether the full Cloudimage transform grammar is accepted
> verbatim on the `<token>.filerobot.com` delivery domain was not confirmed
> against a live project. `w`, `h`, `q` and `f=auto` are the safe subset to
> assume; test `func`, `gravity`, and the filter params before relying on them.

## Cache invalidation

Purging is a Cloudimage API operation (`api.cloudimage.com`, `X-Client-Key`),
not a DAM one. Both per-URL and per-prefix invalidation exist. Replacing an
asset in the DAM does not guarantee immediate propagation to already-cached
derivatives — invalidate explicitly when you overwrite in place, or avoid the
problem by writing a new filename.
