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
| POST   | `/validate/m11-docx/download/xlsx` | Takes findings JSON in the body, streams an openpyxl workbook |

CSV, JSON, and Markdown downloads are generated entirely client-side in
`static/js/m11_download.js`. The browser reads the findings JSON
embedded in the results page (`data-findings` attribute on
`#m11-download-controls`), builds a `Blob`, and triggers the download.
No server round-trip for those three.

XLSX is the exception: it needs openpyxl (which is already a dependency
via `usdm4_excel`). The browser POSTs the findings JSON to the
`/download/xlsx` endpoint, which renders the workbook and streams it
back with an `attachment` Content-Disposition. The filename is
deterministic: `{source-basename}-m11-findings-{YYYY-MM-DD}.xlsx`.

## Templates

- **`validate/partials/validate_m11_docx.html`** — the picker. Extends
  the shared picker pattern from `import/partials/browser_file_select.html`.
- **`validate/partials/m11_docx_results.html`** — findings table,
  download controls, HTMX out-of-band swap that updates the picker
  card's subtitle to include the validated filename. **Intentionally
  does not `{% extends %}` a layout** — HTMX swaps this partial into
  the picker's `#form_div`; extending would duplicate the page chrome.
- **`studies/list.html`** — the compare view. Title-page tab cells
  render findings in native `<details>`/`<summary>` so the table stays
  compact by default; expand to see finding panels inline. An
  "Expand all / Collapse all" button at the top iterates `<details>`
  elements for demo mode.

## Javascript

- **`static/js/m11_download.js`** — generates CSV / JSON / Markdown
  client-side; POSTs for XLSX. Reads findings from
  `#m11-download-controls[data-findings]` as JSON. Handles filename
  sanitisation and Blob download.
- **Inline in `studies/list.html`** — Bootstrap tooltip init (legacy,
  mostly no-op now that finding text is visible in expanded panels);
  onclick handlers on the Expand-all / Collapse-all buttons.

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
