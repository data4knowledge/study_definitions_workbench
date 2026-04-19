# SDW Lessons Learned

Working notes from building SDW features. Not the SDW architecture or
the M11 rule details — those live in `docs/m11_validation.md` and
(for the rules themselves) the sibling `usdm4_protocol` repo's docs.
This file captures the things that bit us while building, that future
contributors (or future us) should know before re-tripping on them.

New lessons go at the bottom. If a lesson is superseded by a later
insight, edit it in place — this isn't a change log.


## 1. Editable-installed external packages need a manual server restart

uvicorn `--reload` only watches files under the app root (`app/`). When
you edit code in an editable-installed dependency — `usdm4_protocol`,
`usdm4`, `simple_error_log`, `usdm4_fhir`, `d4k-ms-*` — uvicorn does
not notice, and Python's module cache holds the pre-edit version in
memory for the life of the process.

Symptom: you changed something in `usdm4_protocol/m11/validate/` (or
similar), confirmed the file on disk has your edit, the .pyc is newer
than the source, reload the browser, and still see the old behaviour.

Cure: stop uvicorn fully (Ctrl-C) and start it again. The new process
re-imports from source on first request.

Prevention: if you're actively iterating on an external package, start
uvicorn with `--reload-dir /path/to/pkg/src` in addition to the app
root. That widens the watch set.

## 2. HTMX result partials must not extend a layout

SDW's result pages (see `validate/partials/results.html`,
`validate/partials/m11_docx_results.html`) are HTMX-swapped into a
parent page's `#form_div`. If the partial `{% extends %}`s a layout,
the response carries a full `<html>…</html>` page and HTMX drops the
entire chrome (nav, sidebar, footer) inside the parent's chrome —
producing a nested "page within the page" visual bug.

Rule: result partials contain ONLY the content that should appear in
the swap target. No `extends`, no `block` beyond a single
`{% block main_content %}` (which is ignored during the swap anyway
but kept for consistency with page-level templates).

Out-of-band swaps (`hx-swap-oob="true"` on nested elements) are the
correct way to update sibling regions of the parent page — e.g. the
subtitle update on the validate results page.

## 3. DataFiles `media_type` must exist before `save()` / `path()`

`DataFiles` has a registry of named types (xlsx, docx, usdm, pj,
expansion, fhir_prism*, errors, …). Calling `save()` or `path()` with
an unregistered type name raises `KeyError` — but the `save()` method
swallows exceptions silently (`except Exception: return None, None`),
so the crash surfaces later at `path()` time with a confusing
traceback.

Before adding a new flow that writes files, check whether an existing
`media_type` entry fits. If it doesn't, add one to
`DataFiles.__init__`. We hit this once with a proposed `"m11"` type
that turned out to be `"docx"` on closer inspection.

## 4. Pill/badge styling — follow the home-page convention

SDW uses a custom Bootswatch theme (Cosmo-family) with these colour
mappings visible in `static/css/bootstrap.min.css`:

- `--bs-primary: #2780e3` (blue)
- `--bs-info: #9954bb` (**purple** — not Bootstrap default teal)
- `--bs-warning: #ff7518` (deep orange — not Bootstrap default amber)
- `--bs-danger: #ff0039` (crimson)
- `--bs-success: #3fb618` (green)

Consequences:

- **Compact pills** on the home page (`studies/partials/show.html`)
  use `class="badge rounded-pill bg-<name>"` — fully rounded, solid
  colour, default white text. New pills elsewhere should match
  exactly. Miss `rounded-pill` and you get a corner-rounded rectangle;
  miss `text-white` on warning and text is hard to read.
- `bg-info` ≠ informational-grey. It's purple. If you want "grey
  informational" use `bg-secondary`.
- Buttons use `class="btn btn-sm btn-outline-primary rounded-5"` for
  the pill-shaped outlined-primary style seen in `View Details`,
  `Select`, `Sponsors`, `Phases`. Don't reach for `btn-outline-secondary`
  unless you really want the muted look — it stands out wrong against
  SDW's conventions.

## 5. Rehydrate saved errors rather than re-running the pipeline

When a downstream view (e.g. `/studies/list`) needs context that was
computed at import time (e.g. extraction-time normalisation records
from the M11 validator), check whether the pipeline already persists
it. SDW saves `errors.csv` per import via `DataFiles._save_csv_file` —
that file carries the `error_type` tag and a Python-dict-repr `extra`
payload for every INFO+ entry.

`USDMJson.import_errors()` reads that CSV back into an `Errors()`
object. Consumers that filter by `error_type` and read `extra` (the
M11 validator's `_collect_normalisation_findings` /
`_collect_contradiction_findings`) work unchanged against the
rehydrated object.

Two cheats worth knowing:

- DictWriter serialises the `extra` dict by `str()`, not JSON. Parse
  it back with `ast.literal_eval` (safe for literal containers, not
  arbitrary expressions). `json.loads` won't work.
- Unknown / malformed rows should degrade silently to empty payloads,
  not raise. Legacy imports predate the typed-record format; future
  imports may add fields we don't know about yet.

## 6. Don't run pytest while the dev server is up

Both hit the same SQLite database. Test cleanup (`_clean()` helpers in
`tests/conftest.py`) wipes records the server depends on and vice
versa. The `claude.md` "Known issues" section captures the root cause
(module-level singleton + engine-at-import-time in `database.py`,
`TestClient(app)` sharing the app's engine rather than the test
`db` fixture) — a proper fix is on the backlog.

Until then: stop the server before running tests. Obvious in
retrospect; easy to forget in flow.

## 7. Client-side downloads for small structured data; server-side for XLSX

The M11 download row offers four formats (CSV / JSON / Markdown / XLSX).
CSV, JSON, and Markdown are generated entirely in the browser via
`Blob` + `URL.createObjectURL` — zero server round-trip, zero new
route, ~30 lines of JavaScript per format (see
`static/js/m11_download.js`).

XLSX is the exception because we don't ship a client-side XLSX
library. The browser POSTs the findings JSON to
`/validate/m11-docx/download/xlsx`; the server generates the workbook
via openpyxl (already installed via `usdm4_excel`) and streams it
back. No server persistence needed — the data comes from the client.

The pattern generalises: if the data's small enough to embed in the
rendered HTML as a `data-*` attribute and the format has a JS path,
do the download client-side. Fall back to server for formats that
need Python libraries the browser can't easily ship.

## 8. Native `<details>` is a fine toggle — no JS, no framework

The compare view's per-cell finding expand-collapse uses
`<details><summary>…</summary>…</details>` with `list-style: none` on
the summary (to hide the default disclosure triangle when we want a
custom icon). Native browser behaviour handles open/close,
keyboard accessibility, focus state — we write no JavaScript for the
base interaction.

The global "Expand all / Collapse all" buttons DO need a line of JS
each, but it's a one-liner iterating `document.querySelectorAll` and
setting `.open = true|false`. Bootstrap's collapse component would
have been heavier and brought no real value here.

Reach for `<details>` before `data-bs-toggle="collapse"` when the
content is content (not, say, a whole menu panel). Progressive
enhancement, not framework weight.

## 9. Asymmetric UX is a valid stopping point

Early in the M11 validation work we had extraction-time normalisation
findings showing on `/validate/m11-docx` but not on `/studies/list`.
The right fix (persist the trace, rehydrate in the compare view —
lesson 5) eventually landed, but in the meantime "the two views show
different things" was acceptable. The dedicated validate view served
the richer need; the compare view's Wrapper-only findings were
internally consistent with what the compare view displayed.

Related: lesson 69 in `usdm4_protocol/docs/lessons_learned.md` on the
two-channel evidence pattern for M11_042.

When you hit an asymmetry like this during active development, label
it honestly in the UI (not "0 findings" but "0 Wrapper-state
findings") or document it in `next_steps.md` as an open item. Both
are better than pretending the gap isn't there and better than
stopping to build the symmetric fix before the rest is stable.

## 10. The `docs/` and `claude.md` pair is the durable memory

SDW has pytest, but tests don't capture "why we chose this approach."
Add a lesson to this file when you step on one, add a backlog item to
`next_steps.md` when something's scoped but not shipped, and link
both from `claude.md`'s feature-specific-docs list. The next
contributor — including future-you — starts from a complete map
rather than re-deriving.
