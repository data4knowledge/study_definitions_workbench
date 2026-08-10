# SDW project memory

## 2026-07-17 — .test_env was missing; recreated

Dave's pytest run failed at collection: `Configuration()` crashed on `SINGLE_USER` being unset. Root cause: `.test_env` (gitignored) did not exist in the working copy, so both conftest's `load_dotenv` and ServiceEnvironment's `.{env}_env` load were silent no-ops. `.development_env` / `.playwright_env` are also absent — if the dev server or Playwright runs fail the same way, those need recreating too. Recreated `.test_env` with self-contained paths under `tests/test_area/` (all keep paths inside MNT_PATH — the layout the `clean_and_tidy` guard requires; also keeps the test SQLite fully separate from the dev DB, which sidesteps the known test/server DB-corruption trap). Added `tests/test_area/` to .gitignore.

## 2026-07-17 — Backbone load interface added

SDW can now push a study version's USDM v4 JSON into the d4k backbone. Decisions (Dave): config via `BACKBONE_URL` env var (not the Endpoint table); optional `BACKBONE_API_KEY` sent as `X-API-Key` header when set (backbone doesn't enforce auth yet — header choice is SDW's convention, match it backbone-side when auth lands); action lives in the Transmit dropdown on the version summary page, gated by the Transmit role (server-side too, unlike the FHIR transmit route which only gates in the UI).

Files: `app/utility/backbone_transmit.py` (new, mirrors `fhir_transmit.py` — thread + Transmission audit + WebSocket notify, httpx multipart POST to `{BACKBONE_URL}/v1/studies`), `app/routers/versions.py` (route `GET /versions/{id}/backbone/load` + `backbone` key in summary data), `app/templates/shared/partials/transmit_menu.html` (menu item), `app/configuration/configuration.py` (`backbone_url`). Tests: `tests/utility/test_backbone_transmit.py`, additions to `tests/routers/test_versions.py`.

State: py_compile + Jinja-parse verified only — Cowork sandbox can't run the suite (repo .venv is macOS). Dave to run `python -m pytest tests/utility/test_backbone_transmit.py tests/routers/test_versions.py` (server stopped — SQLite corruption trap). Not yet exercised against a live backbone.

## 2026-08-10 — USDM v3 support removed; Excel via usdm4_excel

Branch 71-package-updates. Dave's decisions: drop v3 entirely (import, validation, Excel export). Removed all use of the frozen `usdm` (usdm_db/usdm_excel/usdm_info/usdm_model), `usdm3` and `usdm3_excel` packages. Excel import and export now both go through `usdm4_excel` (`USDM4Excel.from_excel` / `to_excel(..., format="legacy")`). Model version string now from `usdm4.__info__`. `DataStore` (usdm_explore) and `Wrapper` (usdm_json) now from usdm4. Deleted: /import/usdm3 + /validate/usdm3 routes, ImportUSDM3 processor, v3 menu items, tests/test_files/usdm3/. Kept: `ImportManager.USDM3_JSON` constant + `is_usdm3_json_import` — display-only so historical v3 imports still render (source pill, errors file); constructing ImportManager with it now raises KeyError (pinned by test).

Golden files regenerated against usdm4 0.29.0 / usdm4_excel 0.10.0 / usdm4_protocol 0.10.0: tests/test_files/excel/pilot_usdm.json (now v4-shaped) and all four M11 goldens + errors yamls (new output includes administrableProducts, CT 2026-03-27, renumbered ids) — Dave should sanity-check the M11 diffs are expected new behaviour, not blessed bugs. Note: RadVax golden is tracked lowercase (radvax_usdm.json) but the test reads RadVax_usdm.json — works on macOS, breaks on case-sensitive filesystems.

Verified: full suite (minus playwright) 677 passed, 0 failed, on Linux/py3.12 with the three local editable packages. Playwright tests updated (v3 flows removed; test_excel_v3_export deleted as duplicate of the v4 export test; menus test now pins v3 absence) — Dave ran them, remaining suite green. Old `usdm` 0.67.0 still installed in the repo .venv — nothing depends on it any more; `pip uninstall usdm`.

## 2026-08-10 — Multi-design support in views

Approved plan, three items. (1) Version-level Summary/Statistics/Safety pages: tab markup was broken for N>1 designs (every tab/pane marked active, anchors not wired as Bootstrap toggles, and a malformed `class="nav nav-tabs role="tablist"` attribute); now proper tabs, first active only, panes swap with hx-swap="innerHTML" so the tab-pane wrapper survives the HTMX load. (2) Design-level partials (study_designs/summary|statistics|safety.html, partials/timelines.html): element ids were built from `data['uuid']` (never passed — rendered empty) or `data['id']` (version id — same across designs); all now scoped by study_design_id, including timelines' inner Data/Document tab set. (3) Compare view (studies.py): inclusion/exclusion no longer from studyDesigns[0]; now a list of {design, criteria} groups per study, criteria.html prints the design label only when a study has >1 design.

Audit found everything else already multi-design (timeline/SoA routes take study_design_id; USDMJson methods take design id; study_version() builds all designs and joins phases) or design-agnostic (protocol/document views, exports, transmit, validation, diff, history). Out of scope by agreement: exposing usdm4_excel's multi-format export in the export menu; usdm4_protocol document-view audit.

Tests added (not run — Dave runs): test_version_summary_multiple_designs (tabs/aria/innerHTML assertions) in tests/routers/test_versions.py; test_study_list_multi_design_criteria in tests/routers/test_studies.py. Existing: test_multiple_phases already covers two-design study_version(). Suggested run: tests/routers/test_versions.py, tests/routers/test_studies.py, tests/model/test_usdm_json.py, then a browse of /versions/{id}/summary|statistics|safety with the multi-design pilot import.
