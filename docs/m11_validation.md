# M11 Validation in SDW

SDW surfaces the M11 protocol validator from `usdm4_protocol` in two
places:

1. A dedicated validation page at **`/validate/m11-docx`** — upload a
   protocol `.docx`, see findings in a table, download in any of four
   formats.
2. The existing compare view at **`/studies/list`** — per-cell
   validation badges and expandable finding panels alongside the
   protocol values, for up to N selected studies.

The library side of all this lives in `usdm4_protocol` (branch
`8-m11-validation`); see that package's `docs/m11_rule_interpretation.md`
and `docs/m11_observed_issues.md` for what the rules are and why. This
document describes how SDW consumes and presents them.

## Data flow

```
[.docx upload]
       │
       ▼
USDM4M11().validate_docx(path)
       │  runs extraction → wrapper, then M11Validator(wrapper)
       │
       ▼
M11ValidationResults
       │  to_dict() → list[{rule_id, severity, status, message,
       │                    expected, actual, element_name,
       │                    section_number, section_title}]
       │
       ▼
app/routers/validate.py::_process_m11_docx
       │
       ▼
validate/partials/m11_docx_results.html (HTMX-swapped into picker)
```

The compare view (`/studies/list`) takes the same `M11Validator` but
runs it against each selected study's loaded USDM `Wrapper` (no fresh
docx extraction — the findings reflect what's in the stored USDM). The
runner is shared; only the entry point differs.

## Routes

| Method | Path                             | Purpose                                                         |
|--------|----------------------------------|-----------------------------------------------------------------|
| GET    | `/validate/m11-docx`             | File picker (shared `browser_file_select.html`)                 |
| POST   | `/validate/m11-docx`             | Extract + validate; returns the HTMX results partial            |
| POST   | `/validate/m11-docx/download/csv`  | Findings as CSV                                                |
| POST   | `/validate/m11-docx/download/json` | Findings as JSON (pretty-printed)                              |
| POST   | `/validate/m11-docx/download/md`   | Findings as a Markdown document                                |
| POST   | `/validate/m11-docx/download/xlsx` | Findings as an openpyxl-generated workbook                     |

**Downloads are server-side, form-based, and zero-JS.** The results
template emits a plain HTML `<form>` carrying the findings JSON and
source filename as hidden inputs; each of the four submit buttons
uses `formaction` to target one of the routes above. The server
picks up the form-encoded fields, runs the matching formatter in
`app/utility/m11_findings_export.py`, and streams the file back with
a deterministic filename (`{source-basename}-m11-findings-{YYYY-MM-DD}.{ext}`).

The annotated-document view is also zero-JS. Each finding marker is
a native `<details>` element injected by the server-side annotator
(`app/utility/m11_annotate.py`); the browser handles the toggle.

## Templates

- **`validate/partials/validate_m11_docx.html`** — the picker. Extends
  the shared picker pattern from `import/partials/browser_file_select.html`.
- **`validate/partials/m11_docx_results.html`** — findings table +
  download form, plus the annotated-document tab. HTMX out-of-band
  swap updates the picker card's subtitle with the validated filename.
  **Intentionally does not `{% extends %}` a layout** — HTMX swaps
  this partial into the picker's `#form_div`; extending would
  duplicate the page chrome. Pulls in `shared/styles/m11.html` so the
  annotated protocol keeps its existing styling.
- **`studies/list.html`** — the compare view. Title-page tab cells
  render findings in native `<details>`/`<summary>` so the table stays
  compact by default; click a cell's disclosure to see its finding
  panels inline.

## JavaScript policy

**We don't write JavaScript for UI state.** Forms, links, HTMX, and
native `<details>` cover every interaction in this feature. Two stub
files remain in `static/js/` (`m11_download.js` and `m11_annotated_doc.js`)
only to absorb any stale `<script src>` references from browsers with
cached pages — no active template references them, and they contain
no logic. Safe to `git rm` once you've confirmed the templates are
clean.

## Tests

- `tests/routers/test_validate.py` — GET / POST happy, POST with
  failed extraction, POST with no file, XLSX download route (success,
  custom filename, empty findings).
- `tests/routers/test_studies.py` — the compare view renders
  validation badges when `M11Validator` is mocked to return findings.

Run with `pytest --ignore=tests/playwright`. See `claude.md` for the
broader testing note — don't run pytest while the dev server is
running (both hit the same SQLite DB and tests wipe rows).

## Open items

See `docs/next_steps.md` for the running backlog (persistence,
background execution, annotated protocol render, etc.).
