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
validate-docx results page (see archive). Open polish items:

- **Keyboard navigation.** `n` / `p` to cycle through markers, `Esc`
  closes the side panel (already wired). Would also want `g` /
  `shift-G` to jump first/last, and scroll-into-view on focus.
- **Severity filter.** Toggle buttons at the top of the annotated doc
  to hide info-level or warning-level markers when doing a
  triage-pass on errors only.
- **Jump-to-finding from the findings table.** Clicking a row in the
  Findings tab switches to the Annotated document tab and
  scroll-to-highlights the matching marker.
- **Persistent panel-open state across tab switches.** Today
  switching tabs closes the panel; ideally it should remember the
  last-selected finding when you come back.
- **Compact mobile layout.** The side panel is desktop-sized; on
  narrow viewports it should become a bottom-sheet.

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

Shipped on branch `57-add-m11-validation` — CSV, JSON, Markdown
client-side; XLSX via `/validate/m11-docx/download/xlsx`.

### 2. Findings detail on compare view ✅

Shipped on branch `57-add-m11-validation` — native `<details>` per
cell with severity-coloured finding panels and a global Expand-all /
Collapse-all toggle on the title-page tab.

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
Annotated document (new).

Pipeline:

- `usdm4_protocol` side — `M11Export._parse_elements` stamps each
  rendered element with `data-m11-element="<name>"`;
  `USDM4M11.render_current()` re-renders the cached wrapper without
  re-extraction.
- SDW side — `app/utility/m11_annotate.py::annotate()` walks the
  rendered HTML via BeautifulSoup, injects a severity-coloured marker
  inside each `[data-m11-element]` node, returns the annotated HTML
  plus any findings that couldn't be located. `_process_m11_docx`
  calls render + annotate and passes both into the template.
- UI — native `<details>`-free this time; a single fixed side panel
  reveals the finding on marker click. Keyboard-accessible (Enter /
  Space activate markers, Esc closes the panel).

Follow-up polish (keyboard nav, severity filter, jump-from-findings-table,
persistent panel state) is captured in §3a above.
