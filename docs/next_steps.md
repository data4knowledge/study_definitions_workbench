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

### 3. Annotated protocol render

**Problem:** Currently the validator reports findings in a table. Users
can see the findings and they can see the rendered protocol (via the
existing `USDM4M11().to_html(path)` view), but the two are in
different places. For demos, PR, and teaching M11 it would be
compelling to see the rendered protocol with finding markers overlaid
on the offending elements in place.

**Proposed approach:**

- Leverage the existing `to_html()` render, which walks the M11
  template and produces HTML with one visible `<m11:element>` per
  element. The renderer replaces those with the extracted value.
- Decorate post-hoc: after rendering, walk the output, match each
  `<m11:element name="X">`-produced div / span against the findings
  by element name, and inject a severity marker + hover / click
  reveal with the rule message.
- Alternatively, weave the decoration into the renderer itself by
  passing the findings dict in.
- UX: a red/amber/grey bar in the document's margin at the offending
  element, click to expand a side panel with the rule details. Jump
  navigation — next finding / previous finding — via keyboard.
- Probably wants its own route and template distinct from the current
  table-driven results page. Or a tab within the results page
  ("Document view").

**Effort:** medium. Bulk of the work is the decoration walk and the
side-panel UI; the renderer's existing element-by-element traversal
gives a clean attachment point.

**Context:** flagged by Dave as issue 3 during the April 2026
validation UX review. Pure PR value; not blocking.

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
