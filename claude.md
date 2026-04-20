# CLAUDE.md

## Project

Study Definitions Workbench — a FastAPI web application for managing USDM (Unified Study Definitions Model) clinical study data, with FHIR M11 import/export support.

## Interaction layer: HTMX, not hand-written JavaScript

SDW uses HTMX (+ native HTML: forms, links, `<details>`, `<dialog>`, etc.) as its interaction layer. Preference order:

1. Native HTML elements that already do the job (forms, `<details>` / `<summary>`, `<dialog>`, anchors).
2. HTMX attributes (`hx-post`, `hx-swap`, `hx-target`, `hx-swap-oob`, `hx-indicator`, `hx-disabled-elt`).
3. Complete packaged JavaScript libraries with a narrow purpose (e.g. D3 for visualisations on specific pages, a PDF viewer on protocol pages). Library boundaries keep these self-contained.
4. Hand-written JavaScript glue — avoid. It accumulates fast, tangles across files, and drifts from the markup it manipulates.

Before adding any JavaScript, check whether #1 or #2 does the job. Before pulling in a library under #3, check that the feature genuinely needs the library (not just "would be convenient"). When in doubt, ask. See `docs/lessons_learned.md` (lesson 10) for the full reasoning and the M11-validation cleanup that established this stance.

## Feature-specific docs

- **M11 validation UI** — `docs/m11_validation.md`. How the `/validate/m11-docx` and `/studies/list` validation flows work end-to-end, which templates and JS do what, and which routes exist. The rule catalogue and interpretation live in the sibling `usdm4_protocol` package under its `docs/m11_rule_interpretation.md` and `docs/m11_observed_issues.md`.
- **Backlog** — `docs/next_steps.md`. Running list of scoped-but-not-shipped improvements (validation background execution, annotated protocol render, validation history, …). When you finish an item, move it to the Archive section.
- **Lessons learned** — `docs/lessons_learned.md`. Hard-won "don't step on this" notes from building SDW features: the server-restart-for-external-packages trap, HTMX partial pattern, pill-styling convention, DataFiles media-type gotchas, rehydrating saved errors, and why `<details>` beats `data-bs-toggle="collapse"` for small toggles. Add a lesson here when you step on one.

## Tests

There are two distinct types of tests in this project:

### 1. Unit tests (fast, safe to run anytime)

These test individual classes and methods directly, using test data helpers and unittest mocks. They do **not** require a running server or browser.

- `tests/model/` — Tests for `USDMJson` and other model classes. Uses `tests/helpers/usdm_test_data.py` to build minimal USDM data dicts, and `object.__new__()` to bypass `__init__`.
- `tests/database/` — Database model tests.
- `tests/configuration/` — Configuration tests.
- `tests/dependencies/` — Dependency tests.
- `tests/routers/` — Router endpoint tests using FastAPI `TestClient`. Uses mocks from `tests/mocks/` to stub out `USDMJson`, user auth, FHIR versions, etc.
- `tests/test_main.py` — Main app endpoint tests, also using `TestClient` and mocks.
- Other unit test dirs: `tests/excel/`, `tests/fhir/`, `tests/files/`, `tests/imports/`, `tests/m11/`, `tests/usdm/`, `tests/usdm_database/`, `tests/utility/`

Run unit tests (excluding playwright):

```
python -m pytest --ignore=tests/playwright
```

### 2. Playwright end-to-end tests (require browser, slow)

Located in `tests/playwright/`. These require a running server and browser environment. **Do not run these during normal development or CI unless specifically intended.**

## Key test infrastructure

- `tests/helpers/usdm_test_data.py` — Builds minimal USDM study dicts for unit testing model methods.
- `tests/mocks/` — Mock factories for FastAPI endpoint tests (e.g. `usdm_json_mocks.py`, `user_mocks.py`, `fhir_version_mocks.py`).
- `tests/test_files/` — JSON/USDM fixture files used by various tests.

## Common patterns

- USDM data uses CDISC NCI codes as dictionary keys (e.g. `C54149` for Pharmaceutical Company, `C207616` for Official Study Title). Templates and code reference these codes, not human-readable names.
- The `study_version()` method returns identifiers as `{code: {label, identifier}}` dicts, and titles as `{code: text}` dicts.
- FHIR version support is configured in `app/dependencies/fhir_version.py`. Only versions listed in `FHIR_VERSIONS` are valid for export/transmit.

## Known issues

### Test/server database corruption

**Do not run pytest while the dev server is running.** Both can end up using the same SQLite database, and test cleanup (`_clean()` helpers) will wipe records the server depends on.

Root cause: `application_configuration` is a module-level singleton (`app/configuration/configuration.py:36`) and `database.py` creates its engine at import time (lines 6-10), before `conftest.py`'s session fixture loads `.test_env`. Tests using `TestClient(app)` share the app's module-level engine rather than the separate test `db` fixture. This needs fixing — see memory for details.
