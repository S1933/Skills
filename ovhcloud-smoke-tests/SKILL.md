---
name: ovhcloud-smoke-tests
description: Use when OVHcloud smoke-test patterns fail literal HTML matching or the locale-specific pattern catalogue needs updating.
compatibility: Environment-specific; requires the smoke-test repository and access to rendered locale pages.
---

# OVHcloud smoke tests

## Context

- Repo: `<smoke-tests-repository>`, single file `ovhcloud.yml` (~400KB).
- Each entry is a `url` + `pattern` pair under `blue_green_smoke_urls`:
  ```yaml
  -
    url: fr/domains/dnssec
    pattern: 'Protégez vos noms de domaine contre les attaques par usurpation'
  ```
- The test does a **literal substring match** of `pattern` against the exported
  static HTML at `<rendered-html-root>/<locale>/<path>/index.html`. That export
  mirrors the corresponding live locale pages.
- Mojibake in failure logs (`ProtÃ©gez`, `Â«`) is just the log viewer reading UTF-8 as Latin-1. The yml itself is clean UTF-8 — don't "fix" encoding.
- Failures almost always mean the page was redesigned and the old text no longer exists.

## Workflow to fix failing patterns

### 1. Locate the entries

`grep -n '<path-segment>' ovhcloud.yml` (e.g. `dnssec`). A page usually has ~20 entries, one per locale.

### 2. Download the raw HTML for EVERY affected locale

Do not trust one locale per language and copy-paste:
- Regional variants genuinely differ: `en-gb` said "Cheap domain name" while `en`/`en-ca` said "Affordable domain name"; `es` and `es-es` had different copy.
- The full locale list typically seen: fr, en, en-gb, fr-ca, fr-ma, fr-sn, fr-tn, de, en-ca, asia, en-au, en-ie, en-sg, es-es, es, nl, it, pl, pt, en-in.

Use a raw HTTP client that preserves the response bytes. Do not use a tool that
paraphrases page content for exact-match patterns. Python `urllib` is one
portable option:

```python
import ssl
import urllib.request

ctx = ssl.create_default_context()
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30, context=ctx).read().decode("utf-8")
```

Save all pages to the scratchpad (e.g. `<locale>--<page>.html`) so extraction and verification run on the same bytes.

### 3. Pick a stable pattern per locale

Extract candidates from the raw HTML (H1 content, then text chunks right after `<h1>` for the hero subtitle):

```python
i = html.find("<h1")
parts = [p.strip() for p in re.split(r'<[^>]+>', html[i:i+2500]) if p.strip()]
```

Rules of thumb:
- Prefer a distinctive H1; if the H1 is generic (e.g. dnssec pages have H1 = just "DNSSEC"), use the hero subtitle instead.
- Avoid anything with prices/currency ("à partir de 1,99 €/an") — varies per region and changes with promos.
- Avoid single generic words that would match any page (nav, footer).
- The pattern must be one contiguous text node — H1s split across `<span>`s won't match as one string.

### 4. Verify BEFORE writing

For each (locale, pattern), assert `pattern in raw_html` on the downloaded file. All must count ≥ 1. This is the step that catches paraphrase/whitespace/entity mistakes.

### 5. Update the yml

Scripted edit is safest at this scale: for each line matching `url: <target>`, rewrite the following `pattern:` line. Keep single quotes, escape `'` as `''`. Then:
- `python3 -c "import yaml; yaml.safe_load(open('ovhcloud.yml'))"` to validate.
- Review `git diff`.

### 6. Commit

Follow the repository's current branch and base-branch conventions. Suggested
commit style: `fix: update smoke test patterns for <pages> pages`, with a body
explaining the redesign. Commit or push only when the user asks.
