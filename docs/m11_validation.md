# M11 Validation in SDW

SDW surfaces the M11 protocol validator from `usdm4_protocol` in three
places:

1. **Standalone validate page** at `/validate/m11-docx` — upload a
   protocol `.docx`, see findings in a table, download in any of four
   formats. Does **not** persist anything; a one-shot check.
2. **Study-view Validation tab** at `/versions/{id}/validation` — reads
   the findings captured during import for this specific study and
   pairs them with an annotated render of the imported protocol.
3. **Compare view** at `/studies/list` — per-cell badges and
   expandable finding panels on the title-page tab, for up to N
   selected studies. Reads the same persisted findings file as the
   study-view tab.

The library side lives in `usdm4_protocol`; see that package's
`docs/m11_validator_v2_plan.md` for the rule catalogue and
`CLAUDE.md` under "M11 Validator" for the architecture. This document
describes how SDW consumes and presents the findings.

## Architecture shift (April 2026)

The previous generation of the validator ran in-memory against a
loaded USDM `Wrapper`. The current validator is a **standalone
DOCX-layer** check: `M11Validator(docx_path, errors).validate()`
returns a `simple_error_log.Results` object. It never touches the
USDM translator.

Two consequences for SDW:

- **Validation runs once, at import time.** `ImportM11.process()`
  runs the validator against the uploaded `.docx` and persists the
  projected findings as the `m11_validation` DataFiles media type.
  No other flow re-runs the validator.
- **Study-facing views read the file; they don't re-validate.** The
  compare view and the study-view Validation tab both load
  `m11_validation.json` from the study's DataFiles directory. This
  makes them cheap, deterministic, and unaffected by the DOCX being
  present on disk (relevant for legacy imports).

The standalone `/validate/m11-docx` flow is the exception — it's an
ad-hoc one-shot that doesn't persist. It exists for protocol authors
who want to check a DOCX without going through the full import flow.

## Data flow

### Import-time (once per study)

```
[.docx upload via /import/m11]
       │
       ▼
ImportM11.process()
       │
       ├── M11Validator(docx_path, errors).validate() → Results
       │        │
       │        ▼
       │   project_m11_result(results) → list[dict]  (shared row shape)
       │        │
       │        ▼
       │   DataFiles(uuid).save("m11_validation", json.dumps(rows))
       │
       └── USDM4M11().from_docx(...) → Wrapper
                │
                ▼
          …usual import pipeline…
```

The persisted row shape is the canonical finding shape produced by
`app/utility/finding_projections.py::project_m11_result`:
`{rule_id, severity, section, element, message, rule_text, path}`.

### Study-view Validation tab (/versions/{id}/validation)

```
[study-view menu → Validation View]
       │
       ▼
versions.py::get_version_validation
       │
       ├── DataFiles(uuid).generic_path("m11_validation") → path, exists
       │        │ read JSON into `findings`
       │        ▼
       ├── USDM4M11().to_html(usdm.json_path)  → rendered M11 HTML
       │        │ with data-m11-element="..." stamps
       │        ▼
       └── m11_annotate(rendered, findings) → AnnotatedDocument
                │ html with <details> markers inside [data-m11-element]
                │ + unplaced list for findings whose element isn't rendered
                ▼
       study_versions/validation.html
          ├── Findings tab (reuses validate/partials/results.html)
          └── Annotated Protocol tab
```

The DOCX itself is **not** re-validated. Findings are whatever the
import captured. Re-import the source document to refresh.

### Standalone /validate/m11-docx

```
[.docx upload]
       │
       ▼
validate.py::_process_m11_docx
       │
       ├── FormHandler.get_files() → docx bytes saved to temp
       │
       ├── M11Validator(temp_path, errors).validate() → Results
       │
       └── project_m11_result(results) → list[dict]
                │
                ▼
       validate/partials/m11_docx_results.html (HTMX-swapped into picker)
```

### Compare view (/studies/list)

```
[user selects studies, hits Compare]
       │
       ▼
studies.py::study_list
       │
       ▼  per selected study:
studies.py::_m11_validation_for_study(usdm)
       │
       ├── DataFiles(uuid).generic_path("m11_validation") → path, exists
       │        │ read JSON into findings
       │        ▼
       └── group by element → {element: [finding, …]}
                │
                ▼
       studies/list.html cells → native <details> per cell
```

Non-M11 studies (imported from Excel / FHIR / legacy PDF) return an
empty dict; the template renders "0 findings" on those columns.

## Routes

### Standalone validation

| Method | Path                          | Purpose                                                        |
|--------|-------------------------------|----------------------------------------------------------------|
| GET    | `/validate/usdm`              | USDM v4 file picker (validates a USDM JSON against usdm4 rules)|
| POST   | `/validate/usdm`              | Validate and return findings partial                           |
| GET    | `/validate/usdm-rules`        | USDM v4 file picker — same engine, direct entry                |
| POST   | `/validate/usdm-rules`        | Validate and return findings partial                           |
| GET    | `/validate/usdm-core`         | USDM v4 file picker (CDISC CORE engine)                        |
| POST   | `/validate/usdm-core`         | Validate via CORE engine and return findings partial           |
| GET    | `/validate/usdm3`             | USDM v3 file picker (legacy)                                   |
| POST   | `/validate/usdm3`             | Validate v3 and return findings partial                        |
| GET    | `/validate/m11-docx`          | M11 DOCX file picker                                            |
| POST   | `/validate/m11-docx`          | Run `M11Validator` and return findings partial                  |

### Downloads (generic, shared across all validation flows)

| Method | Path                          | Purpose                                                        |
|--------|-------------------------------|----------------------------------------------------------------|
| POST   | `/validate/download/csv`      | Findings as CSV                                                |
| POST   | `/validate/download/json`     | Findings as JSON (pretty-printed)                              |
| POST   | `/validate/download/md`       | Findings as a Markdown document                                |
| POST   | `/validate/download/xlsx`     | Findings as an openpyxl-generated workbook                     |

The download routes are engine-agnostic: they accept a hidden `kind`,
`title`, `sheet_title`, and the findings JSON as form inputs. Every
validation flow posts to the same four endpoints; the hidden fields
slot the flow's slug into the download filename
(`{source-basename}-{kind}-{YYYY-MM-DD}.{ext}`).

### Study-view validation

| Method | Path                          | Purpose                                                        |
|--------|-------------------------------|----------------------------------------------------------------|
| GET    | `/versions/{id}/validation`   | Findings + Annotated Protocol tabs for an M11-origin study     |

The validation menu entry only appears in the Views dropdown when the
study was imported from an M11 DOCX (or a FHIR PRISM2 message derived
from one). For non-M11 studies, the route renders an explanatory
empty state rather than a 404.

## Templates

### Standalone flow

- `validate/partials/validate_m11_docx.html` — the picker. Extends
  the shared picker pattern from `import/partials/browser_file_select.html`.
- `validate/partials/m11_docx_results.html` — findings table +
  download form. **Intentionally does not `{% extends %}` a layout**
  — HTMX swaps this partial into the picker's `#form_div`; extending
  would duplicate the page chrome. The annotated-document tab was
  removed from this flow (it's now the study-view tab); see
  `docs/lessons_learned.md` lesson 2.

### Study-view flow

- `study_versions/validation.html` — tabbed layout. Findings tab
  delegates to `validate/partials/results.html` (the shared row-shape
  table + downloads). Annotated Protocol tab renders the HTML
  returned by `m11_annotate` inside the standard `.outer-div`
  container, so the M11 protocol CSS (`shared/styles/m11.html`)
  applies as usual. Unplaced findings are surfaced in a warning
  banner on the annotated tab so nothing goes missing.
- `shared/partials/version_view_menu.html` — the Views dropdown
  gates the Validation entry behind `data.get('m11')`. The summary /
  protocol / history routes thread `m11` into their data dicts so the
  entry appears from any view.

### Shared results partial

- `validate/partials/results.html` — canonical findings table used
  by four flows (`/validate/usdm`, `/validate/usdm-rules`,
  `/validate/usdm-core`, and the study-view Findings tab). Consumes
  `data['findings']`, `data['messages']`, and the download slug keys
  (`download_kind`, `download_title`, `download_sheet`).

### Compare view

- `studies/list.html` — title-page tab cells render findings in
  native `<details>`/`<summary>` so the table stays compact by
  default. Uses the shared severity vocabulary (`.m11-validation-badge`)
  as the study-view annotated markers.

## Annotator

`app/utility/m11_annotate.py::annotate(html, findings) → AnnotatedDocument`
walks rendered M11 HTML via BeautifulSoup and injects a native
`<details>` marker inside each `[data-m11-element]` node for every
matching finding. The marker body carries the rule id, message, and
section. No client-side JS — the browser handles expand/collapse,
focus, and keyboard.

Depends on the renderer stamping `data-m11-element="<name>"` on each
element wrapper (see `usdm4_protocol/m11/export/m11_export.py`).
Findings whose `element` doesn't match any node in the render come
back in `AnnotatedDocument.unplaced` so the caller surfaces them
separately rather than silently losing them.

Marker styling lives in `shared/styles/m11.html` (the same stylesheet
that drives the plain M11 render). Severities map:

- `error` → crimson left border, red-tinted background, `bi-x-circle-fill`
- `warning` → amber left border, buff background, `bi-exclamation-triangle-fill`
- `info` → grey-blue left border, pale-blue background, `bi-info-circle`

## JavaScript policy

**We don't write JavaScript for UI state.** Forms, links, HTMX, and
native `<details>` cover every interaction in this feature. See
`docs/lessons_learned.md` lesson 10 for the full reasoning.

## Tests

- `tests/routers/test_validate.py` — standalone GET / POST, POST
  with failed extraction, POST with no file, XLSX download route.
- `tests/routers/test_versions.py` — study-view Validation tab
  covering three paths: non-M11 (renders explanatory notice), M11
  with no persisted findings (renders empty-state notice), M11 with
  persisted findings (renders tabs + finding table + annotated
  stub).
- `tests/routers/test_studies.py` — compare view renders validation
  badges when `_m11_validation_for_study` is mocked to return
  findings. The helper itself is mocked at the seam, so refactors of
  its internals (e.g. the import-time persistence switch) don't
  require test churn.

Run with `pytest --ignore=tests/playwright`. See `CLAUDE.md` for the
broader testing note — don't run pytest while the dev server is
running (both hit the same SQLite DB and tests wipe rows).

## Open items

See `docs/next_steps.md` for the running backlog (validation
history, severity filter on the annotated view, mobile layout
tweaks, background execution for the standalone flow).
