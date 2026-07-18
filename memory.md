# SDW project memory

## 2026-07-17 — .test_env was missing; recreated

Dave's pytest run failed at collection: `Configuration()` crashed on `SINGLE_USER` being unset. Root cause: `.test_env` (gitignored) did not exist in the working copy, so both conftest's `load_dotenv` and ServiceEnvironment's `.{env}_env` load were silent no-ops. `.development_env` / `.playwright_env` are also absent — if the dev server or Playwright runs fail the same way, those need recreating too. Recreated `.test_env` with self-contained paths under `tests/test_area/` (all keep paths inside MNT_PATH — the layout the `clean_and_tidy` guard requires; also keeps the test SQLite fully separate from the dev DB, which sidesteps the known test/server DB-corruption trap). Added `tests/test_area/` to .gitignore.

## 2026-07-17 — Backbone load interface added

SDW can now push a study version's USDM v4 JSON into the d4k backbone. Decisions (Dave): config via `BACKBONE_URL` env var (not the Endpoint table); optional `BACKBONE_API_KEY` sent as `X-API-Key` header when set (backbone doesn't enforce auth yet — header choice is SDW's convention, match it backbone-side when auth lands); action lives in the Transmit dropdown on the version summary page, gated by the Transmit role (server-side too, unlike the FHIR transmit route which only gates in the UI).

Files: `app/utility/backbone_transmit.py` (new, mirrors `fhir_transmit.py` — thread + Transmission audit + WebSocket notify, httpx multipart POST to `{BACKBONE_URL}/v1/studies`), `app/routers/versions.py` (route `GET /versions/{id}/backbone/load` + `backbone` key in summary data), `app/templates/shared/partials/transmit_menu.html` (menu item), `app/configuration/configuration.py` (`backbone_url`). Tests: `tests/utility/test_backbone_transmit.py`, additions to `tests/routers/test_versions.py`.

State: py_compile + Jinja-parse verified only — Cowork sandbox can't run the suite (repo .venv is macOS). Dave to run `python -m pytest tests/utility/test_backbone_transmit.py tests/routers/test_versions.py` (server stopped — SQLite corruption trap). Not yet exercised against a live backbone.
