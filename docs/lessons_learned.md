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

## 7. Server-side downloads via a single HTML form

[Superseded and re-scoped by lesson 10 — the original advice favoured
client-side generation for CSV/JSON/Markdown and server-side for
XLSX. The superseding reasoning is there.]

All four findings downloads (CSV, JSON, Markdown, XLSX) are now
server-side routes. The template carries a single `<form>` with four
submit buttons, each using `formaction` to target the right route.
The shared formatter helper (`app/utility/m11_findings_export.py`)
keeps format code in one place; each route is a thin wrapper around
its `to_*` function. Zero JavaScript, honest round-trip cost,
consistent filename convention across all four formats.

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

## 10. HTMX is SDW's interaction layer; hand-written JavaScript isn't

SDW's stance on client-side code, in order of preference:

1. **Native HTML** — forms, links, `<details>`, `<dialog>`,
   `<summary>`. The browser already handles expand/collapse,
   keyboard interaction, focus management, accessibility.
2. **HTMX attributes** — `hx-post`, `hx-get`, `hx-swap`,
   `hx-target`, `hx-swap-oob`, `hx-indicator`, `hx-disabled-elt`.
   Interaction state stays declarative, in the markup, close to
   the thing it controls. No separate JS file to drift out of
   sync with the HTML it manipulates.
3. **Complete, packaged libraries with a narrow purpose** — D3 on
   a visualisation page, a PDF viewer on a protocol-render page,
   a charting library where charts are the point. Fine. These
   come with their own design and documentation; they don't get
   messy because they're an external dependency with a clear
   boundary.
4. **Hand-written JavaScript glue** — avoid. This is the thing
   that grows, gets tangled across files, drifts from the markup
   it's tied to, and resists testing.

The M11 validation views were an early fall into category 4: a
download script building CSV/JSON/Markdown via `Blob`, a side
panel with click/keyboard/click-outside handlers, an Expand-all
button, a Bootstrap tooltip init. Every piece small; collectively
~280 lines of JS across two files. Rewritten to:

- **Downloads**: one `<form>` with four `formaction`-targeted
  submit buttons against per-format server routes.
  `app/utility/m11_findings_export.py` is the shared formatter;
  each route is five lines.
- **Annotated-document markers**: native `<details>` /
  `<summary>` injected by the server-side annotator
  (`app/utility/m11_annotate.py`).
- **Expand-all / Collapse-all**: removed. Users click cells
  individually.
- **Bootstrap tooltip init**: removed.

Trade-offs we took:

- The shared side panel became inline `<details>` expansions.
  Multiple can be open at once; the tab becomes taller. Still
  readable; arguably clearer for linear review of the protocol.
- Downloads cost a round-trip. Findings are kilobyte-sized,
  imperceptible in practice.
- Server has four download endpoints instead of one. Duplication
  is trivial; the per-format file names and content types are
  clear at the URL level, which helps debugging and scripting.

**Lesson: Default to HTMX and native HTML. Reach for a packaged JS
library when the feature needs something only that library does
(D3 for a chart, a PDF viewer for a rendered document). Treat
hand-written JS glue as the last resort — by the time you notice
it accumulating, it's already hard to untangle.**


## 11. htmx major bumps need each extension refreshed separately

htmx 2.x split its extensions out of the core repo into their own
packages (`htmx-ext-ws`, `htmx-ext-sse`, `htmx-ext-response-targets`,
etc.). When you upgrade the core library, every self-hosted
extension file needs a matching bump — the htmx-1 extension files
run under htmx-2 but emit a permanent console warning on every page
load, and the extension's internals may drift from what the new
core expects.

Symptom we saw: `htmx.ws.js:10 WARNING: You are using an htmx 1
extension with htmx 2.0.8.` on every page load. The extension
still worked; the warning was the tell.

Pattern:

- Self-hosted htmx files live in `app/static/js/` (`htmx.min.js`
  and each `htmx.<ext>.js`). Don't edit the vendored files by
  hand — refresh them from the canonical source.
- Canonical sources: `https://unpkg.com/htmx-ext-<name>/<name>.js`
  or the GitHub repo `bigskysoftware/htmx-extensions`. Version
  numbers live in the upstream package; pin to latest or a
  specific version as the project prefers.
- When bumping core htmx, walk every `<script src>` in
  `shared/_main_layout.html` / `shared/_home_layout.html` and
  refresh each extension in lockstep.

**Lesson: htmx's major-version boundaries are per-extension, not
repo-wide. A `curl -o` that replaces only the core library leaves
stale extension files sitting next to it. When you see an "htmx
1 extension" warning, that's the signal to refresh the one
file — and a reminder to check whether others need the same.**

**Related cache-busting pattern.** After a vendor-file replace,
browsers often keep serving the old copy from disk cache —
reloads don't help because the URL is unchanged. SDW's shared
layouts now cache-bust every self-hosted vendor script via a
``?v=<version>`` query string (see `shared/_main_layout.html`
and `shared/_home_layout.html`). When you bump an extension or
the core library, bump the `v` in the matching `<script src>`
too; browsers treat the changed URL as a new resource and
refetch automatically. Bootstrap and any future self-hosted JS
follow the same convention.


## 12. Not every console error is ours — browser extensions inject too

Twice this session a confusing `Uncaught Error` appeared in the
browser console from a file called `searchAnalyzer.js`:

    at t.SearchEngineFactory.getSearchEngineAnalyzer
      (searchAnalyzer.js:2:241641)

Nothing in SDW (or `usdm4_protocol`) references `searchAnalyzer`,
`SearchEngineFactory`, or anything search-engine related. Telltale
signs it was a browser extension:

- **Minified single-line JS** — the column offsets `:2:241641`,
  `:2:90878`, etc. are millions of characters into line 2. Our
  bundles are readable, multi-line source.
- **Names that don't match any SDW symbol.** A quick `grep -rln
  SearchEngineFactory` across both repos returned zero matches.
- **Page-agnostic** — the same error appears on `/index`,
  `/validate/m11-docx`, and elsewhere, because the extension
  injects into every page.

Two confirmations:

- **Incognito/Private window.** Most browsers disable extensions
  there by default. Loading `http://localhost:8000/index` in a
  private window removes the noise, proving the source.
- **DevTools Sources tab.** Expand the page's tree; extension
  scripts show under `chrome-extension://<id>/…` so you can see
  which extension is responsible and disable it specifically.

There's nothing to fix in SDW. The extension reads the DOM,
doesn't find what it expects, and logs. It doesn't affect
application behaviour.

**Lesson: Before investigating a console error, check whether the
stack trace's source file exists in your repo. `grep -rln
<symbol-name>` is fast and decisive. If no match, the error is
almost certainly from a browser extension (or another tab's
service worker) — disable extensions in Incognito mode to
confirm, then move on.**


## 13. The `docs/` and `claude.md` pair is the durable memory

SDW has pytest, but tests don't capture "why we chose this approach."
Add a lesson to this file when you step on one, add a backlog item to
`next_steps.md` when something's scoped but not shipped, and link
both from `claude.md`'s feature-specific-docs list. The next
contributor — including future-you — starts from a complete map
rather than re-deriving.


## 14. Capture once at import, read many times — don't re-run the validator per view

The first cut of M11 validation in the compare view re-ran
`M11Validator` per selected study on every `/studies/list` request.
That was the wrong seam: the validator's input (the uploaded `.docx`)
is fixed at import time, its output is the `Results` object, and
several views need the same findings. Re-running per view costs
CPU, varies with whether the original DOCX is still on disk (legacy
imports), and risks drift between views if the validator changes
between a study's import and its later viewings.

The pattern we landed on:

- **Capture at import.** `ImportM11.process()` runs
  `M11Validator(docx_path, errors).validate()` once, projects the
  findings to the canonical row shape (via
  `app/utility/finding_projections.py::project_m11_result`), and
  writes them as the `m11_validation` DataFiles media type next to
  the other per-study artefacts.
- **Read in every view.** The compare view
  (`studies.py::_m11_validation_for_study`) and the study-view
  Validation tab (`versions.py::get_version_validation`) both read
  that JSON file. Neither touches the validator. The compare view
  groups by `element`; the study-view tab pairs the findings with a
  rendered protocol via `m11_annotate`.
- **Standalone flow is the exception.** `/validate/m11-docx` is an
  ad-hoc one-shot — no study, no persistence. It still calls the
  validator directly because that is its entire purpose.

Two payoffs worth naming:

- **Deterministic across views.** Compare-view cell counts and
  study-view tab counts are guaranteed to agree — same file, same
  parser. Before the refactor they could diverge if the validator
  rule set changed between import and viewing.
- **Legacy imports degrade gracefully.** When the `m11_validation`
  file is absent (pre-refactor imports, non-M11 studies), callers
  see an empty list and render "0 findings" rather than crashing or
  attempting to re-validate a `.docx` that may no longer be on disk.

Related to lesson 5 (rehydrate saved errors), but stronger — lesson 5
reuses import-time data for a new view while the primary producer
still runs on-demand; this pattern removes the on-demand run
entirely and makes the file the canonical source.

**Lesson: When a computation's input is fixed at one well-defined
moment (upload, import, commit…) and several views need the same
output, run it there, persist the output in the canonical shape, and
make every view a thin reader. Keep the direct-call path only for
flows where there is no "moment" to attach to (one-shot validates,
ad-hoc tools).**


## 15. External-package caches need the same persistence story as our own files

USDM4's CDISC CORE validation downloads a non-trivial set of
resources the first time it runs: JSONata files, XSD schemas, rules
from the CDISC API, CT packages. Cold-cache runs take several
minutes. USDM4 writes the cache under `platformdirs.user_cache_dir()`
by default — which in a Docker container lands in
`/root/.cache/usdm4/core/` and is wiped on every container restart.
The USDM4 facade accepts a `cache_dir` override exactly because of
this case.

What bit us: SDW instantiated `USDM4()` with no arguments in
`/validate/usdm-core`. Everything looked correct locally (the cache
lived in the host user's home and persisted), but every production
deploy would pay the cold-cache tax from scratch. DataFiles'
`clean_and_tidy()` sweep would also wipe the cache on the first run
after restart even if we put it under `/mount`, because the keep-list
only knew about our own three subdirectories.

The fix has three moving parts, and all three matter:

1. **New env var wired through Configuration.** `CDISC_CORE_CACHE_PATH`
   is read in `Configuration.__init__` like every other path. An
   empty string (unset) means "fall through to the USDM4 platform
   default" — so a deployment that hasn't been upgraded still works,
   it just pays the cold-cache cost.
2. **Threaded into every `USDM4(...)` call site.** The primary site is
   `validate.py::_process` (the only caller of `validate_core`), but
   the import processors and `USDMJson` also pass it through for
   uniformity. That means if anyone later adds a `validate_core`
   call in one of those flows, the cache is already configured —
   they won't re-trip this lesson.
3. **Teach `DataFiles.clean_and_tidy()` about the cache.** Added
   `application_configuration.cdisc_core_cache_path` to the `keep`
   list (guarded by truthiness so the empty-string fallback path
   doesn't append `""`). Without this, the next restart's sweep would
   shred the cache we just asked Docker to persist.

Dockerfile pre-sets `CDISC_CORE_CACHE_PATH=/mount/core_cache`, and the
Fly.io deployment notes got a matching `fly secrets set` line so the
production volume layout stays documented. `.env` also gained the
variable so local dev mirrors the container layout.

**Lesson: When an external package caches expensive downloads to disk
and exposes a configurable path, wire that path through the same
config/env/mount plumbing you use for your own persistent files — and
teach any sweep/cleanup logic to preserve it. A cache that's correct
locally but ephemeral in production is a recurring-cost bug that
won't show up until the first restart after a deploy.**


## 16. USDM rules validation at import time is advisory, not a gate

`ImportUSDM3` and `ImportUSDM4` originally treated a USDM rules failure
as fatal: `self.success = False`, set `fatal_error`, the import never
landed in the studies list. The USDM v4 rules library is now active
enough that real-world files routinely fail at least one rule, which
meant the gate was rejecting files the user actually needed to look at
in the workbench (often *because* they don't conform yet).

Both processors now run validation, persist the findings to the errors
file via the existing `ImportManager` save, and proceed to create the
study record regardless of the rule outcome. Parameter extraction
(`_study_parameters`) is also best-effort — when the wrapper or the
high-level accessors (`first_version`, `phases`, `official_title_text`,
…) raise on a structurally non-conforming file, the processor falls
back to `_fallback_parameters()` (an empty-string dict) so the import
still lands. `Study.study_and_version` already synthesises a record
name via `_set_study_name(file_import)` when the supplied `name` is
empty, so this works end-to-end.

The only path that still surfaces a fatal error is an `ImportUSDM3`
v3 → v4 conversion crash. Without a v4 file there's nothing to save —
we keep the v3 rule findings as the diagnostic the user can act on.

The findings remain visible to the user via the existing errors-file
download and the study view. Don't reinstate the gate without first
finding a way to surface findings as a soft warning that lets the
user proceed — the original gate was protecting the studies list from
"broken" data, but in practice it was hiding the data the user needed
to fix.

**Lesson: Validation that the user already has another way to see and
act on shouldn't double as an admission gate. If a check is advisory
in spirit (you're informing, not refusing), implement it advisory in
code — persist the findings, surface them, and let the user proceed.
Gates that mix "tell me what's wrong" and "refuse to load" punish the
exact users who most need the diagnostic.**
