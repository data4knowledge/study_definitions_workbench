# SDW Next Steps

Running backlog of SDW improvements that have been scoped but not yet
shipped. Organised by feature area. Each entry: what's missing, what
approach has been proposed, rough effort estimate, and the original
discussion context.

When an item lands, move it to an "Archive" section at the bottom with
a pointer to the branch / PR.

## M11 validation

### 1b. Background execution for validation

**Problem:** `/validate/m11-docx` POST runs extraction + validation
synchronously. The browser spinner sits for 10–30s on a clean protocol
and longer with AI paths enabled. User can't walk away and return.

**Proposed approach:**

- A background-job model: the POST enqueues a job, returns immediately
  with a job-id page. The job-id page polls (or subscribes via
  websocket) for status updates. When complete, the findings table
  renders in place.
- Storage: job state (in-flight / complete / failed) + findings in
  SQLite alongside the existing study / version tables. A sparse new
  table `validation_job` keyed by uuid is probably the right granularity.
- Visibility: a "Validations" menu item listing recent jobs with their
  status, so the user can come back later and see completed ones.
- FastAPI has `BackgroundTasks` for simple cases but that still ties
  the response lifetime to the job lifetime; a real background worker
  (Dramatiq, RQ, Celery) or a simple thread-pool with persistent
  state is more appropriate for the 10–30s range.

**Effort:** medium-large. Schema change, a worker, a status page, a
polling/websocket UI. Interacts with the existing `DataFiles`
lifecycle.

**Context:** flagged by Dave as issue 1b during the April 2026
validation UX review.

### 3a. Annotated protocol render — polish (follow-up to ✅ below)

The first cut of the annotated render shipped as a second tab on the
validate-docx results page (see archive). Open polish items,
respecting the project's JS-free stance (lesson 10):

- **Severity filter.** Hide info-level or warning-level markers via
  a CSS-only toggle (radio buttons + adjacent-sibling selectors
  scoped to the annotated-doc container). Lets a reviewer do an
  error-only triage pass without scrolling through info findings.
- **Jump-to-finding from the findings table.** Each finding row
  gets an anchor to its marker's element id; clicking scrolls the
  Annotated-document tab into view at that marker. Needs markers
  to carry a stable id per finding and the tab to be switchable via
  URL hash (`:target` CSS or plain `href="#tab-id"`).
- **Compact mobile layout.** Inline expansions push content down
  on narrow viewports; may want `max-width` constraints or an
  option to show finding panels below the rendered doc rather than
  inline.
- **Collapse-all / expand-all.** Removed in the JS cleanup pass.
  A CSS-only version is possible (form + radio buttons + scoped
  selectors) but not trivially accessible; defer until asked for.

## General

### Study-level validation history

Currently every validation is a one-shot — re-upload, re-validate, no
persisted trail. When validation becomes background + persisted (1b),
the natural follow-on is a "validation history" view per study:
previous validations with timestamps, trend of findings over time,
diff between runs.

### Fix pytest-vs-dev-server database sharing

Both use the same SQLite DB through a module-level singleton, so
running pytest while the dev server is up wipes records the server
depends on (and vice-versa). Root cause documented in `claude.md`
under "Known issues". Proper fix: make `application_configuration` a
factory (not a module singleton) and defer engine creation until
inside the request / test context so `.test_env` loading in
`conftest.py` can take effect before the engine is built. Touches
`app/configuration/configuration.py` and `app/database/database.py`.

**Effort:** medium. Interacts with a lot of callers; migration
likely incremental (ship a factory, migrate routes one by one).

## Archive

### 1a. Download from validate view ✅

Shipped on branch `57-add-m11-validation`. All four formats (CSV,
JSON, Markdown, XLSX) are now server-side routes
(`/validate/m11-docx/download/{csv,json,md,xlsx}`). The template
emits a plain HTML `<form>` with four submit buttons using
`formaction` to target each route; shared formatter helper in
`app/utility/m11_findings_export.py`. **Zero JavaScript** — an
initial cut used client-side `Blob` generation for CSV/JSON/MD plus
a JSON-POST for XLSX, but was rewritten to server-only per the
project's JS-free stance (see `docs/lessons_learned.md` lesson 10).

### 2. Findings detail on compare view ✅

Shipped on branch `57-add-m11-validation` — native `<details>` per
cell with severity-coloured finding panels. The global Expand-all /
Collapse-all toggle was removed in the JS-free cleanup pass; users
click individual cells to expand.

### Original M11 validate view ✅

Original shipping of the dedicated `/validate/m11-docx` route — see
`docs/m11_validation.md`.

### Extraction-time findings surface in the compare view ✅

Shipped on branch `57-add-m11-validation`. `USDMJson.import_errors()`
reads the saved `errors.csv` from the study's `DataFiles` and rebuilds
an `Errors()` object, preserving the `error_type` tag and the `extra`
payload. `studies.py:study_list` passes it to `M11Validator` so
normalisation (`M11_010/011`) and contradiction (`M11_042`) findings
surface in the compare view the same way they do in the dedicated
validate view. Uses the existing on-disk CSV format — no schema
change.

### Annotated protocol render ✅

Shipped on branch `57-add-m11-validation`. The validate-docx results
page now has two tabs: Findings (existing table + downloads) and
Annotated document.

Pipeline:

- `usdm4_protocol` side — `M11Export._parse_elements` stamps each
  rendered element with `data-m11-element="<name>"`;
  `USDM4M11.render_current()` re-renders the cached wrapper without
  re-extraction.
- SDW side — `app/utility/m11_annotate.py::annotate()` walks the
  rendered HTML via BeautifulSoup and injects a native `<details>`
  marker inside each `[data-m11-element]` node carrying the rule id,
  message, and expected/actual inline in the `<details>` body.
  Unmatched findings come back in `AnnotatedDocument.unplaced` so the
  caller can surface them separately.
- UI — **zero JavaScript**. Native browser `<details>` handles
  expand/collapse and keyboard interaction. An earlier cut used a
  fixed side panel driven by JS; that was rewritten to inline
  `<details>` per the project's JS-free stance (see
  `docs/lessons_learned.md` lesson 10).
