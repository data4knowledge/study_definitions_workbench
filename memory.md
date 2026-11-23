# SDW project memory

## 2026-11-20 — Issue 79: a file that does not load into usdm4 is refused, not crashed on; repo ruff-clean

Branch `79-invalid-uuid`. Only this repo changed.

**What it was.** A USDM v4 JSON whose `study.id` was a 16-character hex string, not a UUID, imported as "Success". Opening its summary page then raised. `USDM4.loadd` catches the pydantic validation error and returns `None`. `USDMJson.__init__` kept that `None` as the wrapper, so `study_version()` failed on `self._wrapper.study`. `ImportUSDM4` ran the rules library but never loaded the file into the model, so nothing stopped it at import.

**What changed.**
- `app/model/usdm_load.py` (new) — `load_usdm4(usdm4, data)` raises `USDMLoadException` when `loadd` returns `None`. `validation_problems` re-validates to list one `field.path: reason` line per error, since `loadd` keeps them only as text with a traceback.
- `app/model/exceptions.py` — `USDMLoadException(problems)`.
- `app/model/usdm_json.py` — `__init__` loads through `load_usdm4`.
- `app/main.py` — handler for `USDMLoadException` renders `errors/error.html` with "The stored file for this version failed USDM v4 validation: …". One handler covers all ~40 `USDMJson(...)` call sites.
- `app/imports/import_processors.py` — `ImportUSDM4.process` loads the file after the rules run. On failure the import fails with "the file is not valid USDM v4: …", and the rule findings still go to the errors file. Docstring updated.
- Tests: `tests/model/test_usdm_load.py` (new), `USDMLoadException` in `tests/model/test_exceptions.py`, `test_process_model_load_failure_fails_import` in `tests/imports/test_import_processors.py`.
- Ruff: the venv's ruff 0.16.3 has a wider default rule set, and the repo had no config, so `ruff check` reported 328 errors. New `ruff.toml` tells B008 that `fastapi.Depends`, `Form`, `File`, `Query`, `Path`, `Body`, `Header` and `Cookie` are immutable calls (93 hits). 134 unused unpacked variables got a `_` prefix. The 47 catch-all `except Exception` got `# noqa: BLE001`. The rest were fixed in code:
  - mutable `{}` defaults became `None` with the old value restored inside
  - implicit `Optional` became `X | None`
  - `True if x else False` became `bool(x)`
  - `open()` now uses `with`
  - `subprocess.run(..., check=False)`
  - `ClassVar` on `HunkLine.TYPE_TO_STYLE`
  - the findings-export date comes from `_today()` (local date)
  - the local-files timestamp is local time in the same format
  - backbone transmit and the M11 findings read go through `asyncio.to_thread`
  - `scripts/site_populate_http.py` made executable
  - a bare `mock_usdm4.call_count == 2` in the import tests became an assert
- `ruff format` also reflowed `app/utility/service.py`, `tests/mocks/factory_mocks.py`, `tests/model/test_usdm_json.py` and `tests/test_main.py`, formatting only.

**Figures.** Dave's first run: 734 passed, 6 failed. All 6 were golden files: the Excel pilot and the four M11 files, because local usdm4_excel and usdm4_protocol now report 0.12.0 and their generated ids changed. Dave regenerated the goldens, and his final run passed.

**Rejected.**
- Refusing every file that fails the rules at import. Lesson 16 keeps rules advisory, so only a model-load failure refuses.
- Narrowing the catch-all excepts. Tests drive those paths with `side_effect=Exception(...)`.
- Rewriting the 93 FastAPI signatures to `Annotated[...]`. A config entry covers it.

## 2026-11-20 — Issue 80: validation findings download reads saved findings by id

Branch `80-validation-export-fail`. Only this repo changed.

**What it was.** The validation results page put the whole findings list in one hidden form field, and each download button posted it back to `/validate/download/{fmt}`. Starlette 1.6 caps a form field at 1 MB (`max_part_size`). A USDM file with many findings went over that, and the route answered `{"detail": "Field exceeded maximum size of 1024KB."}` before any SDW code ran.

**What changed.**
- `app/model/file_handling/data_files.py`:
  - new `validation_findings` media type
  - `remove(type)` deletes one file and keeps the directory
  - `prune_validation_findings(max_age_seconds=24h)` deletes directories that hold only `validation_findings.json` and are older than a day, so import directories are never matched
- `app/routers/validate.py`:
  - The USDM (CDISC, d4k) and M11 flows used to delete the whole directory after validating. They now prune first, then run `_keep_findings`: remove the upload, save the findings and return the directory id as `findings_id`.
  - The download routes take `findings_id`. `_load_findings` accepts only a UUID, because the id becomes a directory name. It reads `validation_findings`, falling back to `m11_validation`. A missing file gives a 404 with "Run the validation again".
- `app/routers/imports.py` (`/import/{id}/m11-validation`) and `app/routers/versions.py` (version Validation tab) — both include the same results partial for the `m11_validation` file saved at import. They now pass the import's DataFiles uuid as `findings_id`, only when findings exist.
- `app/templates/validate/partials/results.html` — the form posts `findings_id`, not `findings`. It is rendered only when an id is present.
- Tests:
  - `tests/routers/test_validate.py`: downloads go through a patched `DataFiles`, plus a missing id (404 ×4 formats), non-UUID and `../` ids, a download over 1 MB, the `m11_validation` fallback, and the M11 flow removing the upload and saving findings
  - `tests/model/file_handling/test_data_files.py`: prune and remove against `tmp_path`
  - `tests/routers/test_imports.py`: the form carries `findings_id` and not `findings`

**Figures.** Dave's first run: 752 passed, 1 failed, `test_import_m11_validation`. The import and version pages had lost their download form because they passed no id. After the fallback fix Dave's tests passed.

**Rejected.** Raising `max_part_size` on the download routes. Every results page would still embed megabytes of findings and post them back on each download.
