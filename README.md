# Study Definitions Workbench

The swiss army knife for USDM study definitions — a FastAPI + HTMX web
application for managing clinical study data expressed in the CDISC
TransCelerate USDM (Unified Study Definitions Model). Imports ICH M11
`.docx` protocols, validates them against the M11 specification and
against USDM rules (including CDISC CORE), exchanges studies as HL7
FHIR M11 messages, and renders them in a set of comparison and
protocol views.

---

## Quickstart (local development)

```bash
pip install -r requirements.txt
cp .env.example .env   # or edit the committed .env for local defaults
./dev_server.sh        # runs uvicorn on :8000
```

`.env` ships with single-user defaults (`SINGLE_USER=True`, no Auth0
required) and `mount/` sub-paths so the database, data files, local
files, and CDISC CORE cache all land under `./mount` inside the repo.

For the full deployment story — Docker Compose, Docker Run, Docker
Desktop, Fly.io, persistent volumes, and which environment variables
come pre-set inside the published Docker image — see
[`docs/deployment.md`](docs/deployment.md).

---

## Environment Variables

### Authentication (only required when `SINGLE_USER=False`)

In single-user mode all Auth0 variables can be omitted entirely. In
multi-user mode every variable below must be supplied.

| Variable                   | Description                              |
| :------------------------- | :--------------------------------------- |
| `AUTH0_SESSION_SECRET`     | Session secret                           |
| `AUTH0_DOMAIN`             | Auth0 domain                             |
| `AUTH0_CLIENT_ID`          | Auth0 client id                          |
| `AUTH0_CLIENT_SECRET`      | Auth0 client secret                      |
| `AUTH0_AUDIENCE`           | Auth0 audience key                       |
| `AUTH0_MNGT_CLIENT_ID`     | Auth0 management API client id           |
| `AUTH0_MNGT_CLIENT_SECRET` | Auth0 management API client secret       |

### Application

| Variable                | Description                                                                                                                                                                                                                                                    |
| :---------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SINGLE_USER`           | `True` for single-user mode (no auth), `False` for multi-user (Auth0 required)                                                                                                                                                                              |
| `FILE_PICKER`           | `browser` for standard browser uploads, `os` for the built-in server-side picker                                                                                                                                                                            |
| `ROOT_URL`              | The server's base URL (deprecated but still accepted)                                                                                                                                                                                                       |
| `MNT_PATH`              | Root mount path for persistent storage                                                                                                                                                                                                                       |
| `DATABASE_PATH`         | Directory where the SQLite database resides                                                                                                                                                                                                                  |
| `DATABASE_NAME`         | Database filename (e.g. `production.db`)                                                                                                                                                                                                                     |
| `DATAFILE_PATH`         | Directory for uploaded/generated data files                                                                                                                                                                                                                  |
| `LOCALFILE_PATH`        | Directory for local working files within the volume                                                                                                                                                                                                          |
| `CDISC_CORE_CACHE_PATH` | Directory for the CDISC CORE validation cache (rules, JSONata files, XSD schemas, CT packages). Put it on the mounted volume (e.g. `/mnt/<name>/core_cache`) so a cold cache — which can take several minutes to rebuild — survives container restarts. Leave unset to fall through to the USDM4 platform default (ephemeral in a container). |
| `ADDRESS_SERVER_URL`    | URL for the external address server                                                                                                                                                                                                                          |

When running via Docker, the `Dockerfile` pre-sets `MNT_PATH`,
`DATABASE_PATH`, `DATABASE_NAME`, `DATAFILE_PATH`, `LOCALFILE_PATH`,
`CDISC_CORE_CACHE_PATH`, and `ADDRESS_SERVER_URL`, so only
`SINGLE_USER`, `FILE_PICKER`, `ROOT_URL`, and (if multi-user) the
Auth0 variables need to be supplied externally.

---

## Docker (summary)

SDW stores its database, data files, local files, and CDISC CORE
cache under `/mount` inside the container — **a Docker volume must
be mounted there or all data is lost on container stop**. There are
two paths:

### Docker Compose (recommended)

```bash
docker build . -t data4knowledge/sdw:latest
docker compose up
```

`compose.yml` declares a named volume `sdw_data` mounted at `/mount`.
Compose **creates it automatically on first `up` and reuses it on
subsequent `up`s** — you do not need to run `docker volume create`.
Use `docker compose down` to stop while keeping your data;
`docker compose down -v` wipes the volume.

Set environment variables via a `.docker_env` file (referenced by
`compose.yml`). Minimum for single-user mode:

```
SINGLE_USER=True
FILE_PICKER=browser
```

### Plain `docker run` (manual)

If you're not using Compose, create the volume yourself first:

```bash
docker build . -t data4knowledge/sdw:latest
docker volume create sdw_data
docker run -d \
  --mount source=sdw_data,target=/mount \
  -p 8000:8000 \
  --env-file .env \
  data4knowledge/sdw:latest
```

> **Heads-up:** The volume Compose manages and a volume you create
> manually with `docker volume create sdw_data` are **not the same
> volume** — Compose prefixes the name with the project directory.
> Pick one path per environment and stick with it. See
> [`docs/deployment.md`](docs/deployment.md) for the full walkthrough
> and for Docker Desktop / Fly.io / multi-platform publishing.

---

## Fly.io (summary)

Two environments, each with its own `.toml`:

- `fly_production.toml` — app `d4k-sdw`
- `fly_staging.toml` — app `d4k-sdw-staging`

Set secrets on one line:

```bash
fly secrets set -a d4k-sdw \
  MNT_PATH="/mnt/sdw_data" \
  DATABASE_PATH="/mnt/sdw_data/database" \
  DATABASE_NAME="production.db" \
  DATAFILE_PATH="/mnt/sdw_data/datafiles" \
  LOCALFILE_PATH="/mnt/sdw_data/localfiles" \
  CDISC_CORE_CACHE_PATH="/mnt/sdw_data/core_cache"
```

Deploy against the matching `.toml`:

```bash
fly deploy -c fly_production.toml
```

Full Fly.io walkthrough (volumes, single-machine constraint, staging
vs production) lives in [`docs/deployment.md`](docs/deployment.md).

---

## Tests

Two suites, with very different cost profiles:

```bash
# Unit tests — fast, safe to run any time
python -m pytest --ignore=tests/playwright

# Playwright end-to-end tests — require a running server + browser
python -m pytest tests/playwright
```

Do **not** run pytest while the dev server is up — both processes
share a SQLite database through a module-level singleton and test
cleanup will wipe records the server depends on. See
[`claude.md`](claude.md) (§ *Known issues*) for the root cause and
planned fix.

---

## Documentation

- [`docs/deployment.md`](docs/deployment.md) — full deployment guide
  (Docker Compose, Docker Run, Docker Desktop, Fly.io, volumes, env
  vars).
- [`docs/m11_validation.md`](docs/m11_validation.md) — M11 validation
  UI end-to-end: import-time single-run validator, study-view
  Validation tab, compare-view per-cell findings, standalone
  `/validate/m11-docx` flow, routes, and templates.
- [`docs/next_steps.md`](docs/next_steps.md) — running backlog of
  scoped-but-not-shipped improvements.
- [`docs/lessons_learned.md`](docs/lessons_learned.md) — durable
  "don't step on this" notes from building SDW features (HTMX
  patterns, DataFiles gotchas, the external-package cache persistence
  story for CDISC CORE, etc.).
- [`claude.md`](claude.md) — project orientation for contributors and
  AI agents (architecture stance, test philosophy, known issues).

---

## Deployment Checklist

1. Unit tests pass (`python -m pytest --ignore=tests/playwright`)
2. Deploy to staging and verify
3. Playwright end-to-end tests pass
4. Deploy to production and verify
5. Build and push the Docker image (tagged with version **and**
   `latest`)
6. Tag the release in GitHub
7. Check pFDA
8. Write GitHub release notes
9. Update version and release notes for the next release
