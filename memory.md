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
