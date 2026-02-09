# CLAUDE.md

## Project

Study Definitions Workbench — a FastAPI web application for managing USDM (Unified Study Definitions Model) clinical study data, with FHIR M11 import/export support.

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
