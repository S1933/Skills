# Filerobot search grammar (`q=`)

Applies to `GET https://api.filerobot.com/<token>/v5/files?q=…`.

Auth: `X-Filerobot-Key: <api-key>`.

## Operators

| Syntax | Meaning | Example |
|---|---|---|
| `field:value` | equals | `q=asset_type:Photo` |
| `"…"` | quote values containing spaces | `q=asset_type:"Product shot"` |
| `+` | AND | `q=asset_type:Photo+topic:Sovereignty` |
| `,` | OR (within one field) | `q=product:BareMetal,PublicCloud` |
| `-` | NOT | `q=product:-legacy` |
| `field:empty` | field has no value | `q=credit:empty` |
| `field:non-empty` | field has any value | `q=credit:non-empty` |
| `>` `<` `>=` `<=` | numeric / date comparison | `q=width>=1920` |
| `..` | inclusive range | `q=size:100000..500000` |
| `~` | contains, **exact match only** | `q=title~"Bare Metal"` |
| `"phrase"` alone | untargeted fuzzy search | `q="bare metal server"` |

A field key with a space must be quoted as a whole: `q="rights expiry">2026-07-29`.

URL-encode the query string. `+` is significant — encode a literal plus in a
value as `%2B`, and be careful with client libraries that turn `+` into a space.

## Behaviour by field type

| Metadata field type | Supported operators | Retrieval quality |
|---|---|---|
| `SELECT` | `:`, `,`, `-`, `empty`, `non-empty` | Best — use for anything you filter on |
| `MULTI_SELECT` | same as SELECT | Best |
| `TEXT` | `~` only, exact substring | Poor |
| `TEXTAREA` | `~` only, exact substring | Poor |
| `DATE` | `>` `<` `>=` `<=` `..` | Good |
| `NUMBER` | `>` `<` `>=` `<=` `..` | Good |
| `BOOLEAN` | `:true` / `:false` | Good |

**Design consequence.** Because TEXT and TEXTAREA match exactly, free-text
fields (title, description, alt text, caption) are unreliable as retrieval
keys. Any attribute an automated consumer needs to filter on must be modelled
as a SELECT or MULTI_SELECT with a closed vocabulary. Retrofitting this later
means re-tagging the library.

## Native filters

These exist without being declared as custom metadata:

| Filter | Values |
|---|---|
| `type` | `image`, `video`, `document`, `audio`, `archive`, … |
| `mimetype` | e.g. `image/png` |
| `orientation` | `landscape`, `portrait`, `square` |
| `resolution` | numeric comparison, in pixels |
| `size` | bytes, numeric comparison |
| `width` / `height` | numeric comparison |
| `labels` | auto-tagging labels |
| `faces` | number of detected faces — requires the face-detection post-process |
| `color` | dominant colour — requires the colour post-process |

`faces` and `color` return nothing unless the corresponding AI post-process is
enabled on the project *and* the assets were processed after enabling it.
Existing assets need a re-process.

## Reserved keywords

Cannot be used as custom metadata field keys, because they collide with the
native filters above or with internal fields:

`type` · `orientation` · `mimetype` · `color` · `resolution` · `faces` ·
`approval_status` · `enable_favorited`

If a governance document mandates fields named "Asset type" or "Status", map
them to non-colliding keys (`asset_type`, `lifecycle_status`) before creating
the taxonomy.

## Pagination and sorting

| Param | Notes |
|---|---|
| `limit` | page size |
| `offset` | zero-based |
| `order` | e.g. `created_at,desc` / `filename,asc` |

Responses report a total count, so paginate on that rather than looping until
an empty page.

## Related endpoints

- `GET /<token>/v5/files` — search (this grammar)
- `GET /<token>/v5/get/<file_uuid>` — fetch one asset by UUID
- `GET /<token>/v5/folders` — folder tree
- `GET /<token>/v5/meta` — list metadata field definitions, with their types;
  call this first when writing a query against an unfamiliar project
