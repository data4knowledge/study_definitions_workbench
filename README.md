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

`.env` ships with single-user defaults (`SINGLE_USER=True`, no login
required) and `mount/` sub-paths so the database, data files, local
files, and CDISC CORE cache all land under `./mount` inside the repo.
Single-user mode still needs a `SESSION_SECRET` (see below).

For the full deployment story — Docker Compose, Docker Run, Docker
Desktop, Fly.io, persistent volumes, and which environment variables
come pre-set inside the published Docker image — see
[`docs/deployment.md`](docs/deployment.md).

---

## Environment Variables

### Authentication & login

SDW uses **passwordless email-code login** (a short numeric code is
emailed to the user, who enters it to sign in). This replaced the old
Auth0 / OAuth integration — there are no `AUTH0_*` variables any more
(the legacy `AUTH0_SESSION_SECRET` name is still accepted as a fallback
for `SESSION_SECRET`, nothing else).

There are two modes, selected by `SINGLE_USER`:

- **Single-user (`SINGLE_USER=True`)** — no login screen at all. The app
  runs as a single built-in user with full (`Admin` + `Transmit`)
  rights. Nothing needs emailing, so **no SMTP is required**. This is the
  default for local/desktop/PRISM use.
- **Multi-user (`SINGLE_USER=False`)** — email-code login. Users
  self-register, receive a code by email, and sign in. **SMTP must be
  configured** so codes can be sent. Roles live in the user table; any
  `@data4knowledge.dk` email automatically gets `Admin` + `Transmit`.

| Variable                    | Required            | Description                                                                                                    |
| :-------------------------- | :------------------ | :------------------------------------------------------------------------------------------------------------- |
| `SESSION_SECRET`            | **always**          | Signs the session cookie. Set a long random string. (Legacy `AUTH0_SESSION_SECRET` still works.)               |
| `SMTP_HOST`                 | multi-user          | SMTP server host. If unset, codes are logged to the console instead of emailed (dev mode).                     |
| `SMTP_PORT`                 | multi-user          | SMTP port (default `587`).                                                                                      |
| `SMTP_USER`                 | multi-user          | SMTP username.                                                                                                  |
| `SMTP_PASSWORD`             | multi-user          | SMTP password (keep it a secret / Fly secret).                                                                 |
| `SMTP_FROM`                 | multi-user          | From address for the code email (defaults to `SMTP_USER`).                                                      |
| `REGISTRATION_NOTIFY_EMAIL` | optional            | If set, this address is emailed whenever someone self-registers.                                               |
| `EMAIL_DEV_MODE`            | optional            | `true` = log codes instead of emailing. Defaults `true` when `SMTP_HOST` is unset. **Off/unset in production.** |
| `CODE_LENGTH`               | optional            | Login code length (default `6`).                                                                               |
| `CODE_EXPIRY_MINUTES`       | optional            | Minutes a code stays valid (default `10`).                                                                     |
| `DEV_LOGIN_CODE`            | optional (dev only) | Fixed code used **only** in dev mode (Playwright). Ignored in production. See `playwright_server.sh`.          |

> **Production gotcha:** if `SINGLE_USER=False` and no `SMTP_HOST` is set
> (or `EMAIL_DEV_MODE=true`), codes are only logged, never emailed — and
> nobody can log in. Always configure SMTP for a real multi-user deploy.

### Single-user mode — minimum config

```
SESSION_SECRET="<a long random string>"
SINGLE_USER=True
FILE_PICKER=os            # or 'browser'
# plus the storage paths below (or rely on the Docker defaults)
```

No SMTP, no user seeding, no registration needed.

### Multi-user mode — minimum config

```
SESSION_SECRET="<a long random string>"
SINGLE_USER=False
FILE_PICKER=browser
SMTP_HOST="smtp.example.com"
SMTP_PORT=587
SMTP_USER="no-reply@example.com"
SMTP_PASSWORD="<smtp password>"
SMTP_FROM="no-reply@example.com"
REGISTRATION_NOTIFY_EMAIL="admin@example.com"   # optional
```

Getting the first user in: anyone with an `@data4knowledge.dk` address
can self-register at `/register` (they auto-get Admin + Transmit). For
any other first admin, seed one directly:

```bash
python -m scripts.seed_user --email you@example.com --name "Your Name" --roles Admin,Transmit
```

Admins then grant `Admin` / `Transmit` to other registered users at
`/users/manage`.

### Application / storage

| Variable                | Description                                                                                                                                                                                                                                                    |
| :---------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SINGLE_USER`           | `True` for single-user mode (no login), `False` for multi-user email-code login                                                                                                                                                                            |
| `FILE_PICKER`           | `browser` for standard browser uploads, `os` for the built-in server-side picker                                                                                                                                                                            |
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
`SESSION_SECRET`, `SINGLE_USER`, `FILE_PICKER`, and (if multi-user) the
SMTP variables need to be supplied externally.

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
SESSION_SECRET="<a long random string>"
SINGLE_USER=True
FILE_PICKER=browser
```

For multi-user mode add `SINGLE_USER=False` plus the `SMTP_*` variables
(see the Authentication section) so login codes can be emailed.

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

Config on Fly comes from **secrets**, not the committed `.staging_env` /
`.production_env` files (those are dockerignored and only kept as a
reference for what to set). Set storage paths, the session secret, and —
for multi-user — the SMTP settings:

```bash
fly secrets set -a d4k-sdw \
  MNT_PATH="/mnt/sdw_data" \
  DATABASE_PATH="/mnt/sdw_data/database" \
  DATABASE_NAME="production.db" \
  DATAFILE_PATH="/mnt/sdw_data/datafiles" \
  LOCALFILE_PATH="/mnt/sdw_data/localfiles" \
  CDISC_CORE_CACHE_PATH="/mnt/sdw_data/core_cache" \
  SESSION_SECRET="<a long random string>" \
  SINGLE_USER=False \
  FILE_PICKER=browser \
  SMTP_HOST="asmtp.dandomain.dk" \
  SMTP_PORT=587 \
  SMTP_USER="no-reply@d4k.dk" \
  SMTP_PASSWORD="<smtp password>" \
  SMTP_FROM="no-reply@d4k.dk" \
  REGISTRATION_NOTIFY_EMAIL="dih@data4knowledge.dk"
```

Do **not** set `EMAIL_DEV_MODE=true` in production — codes would be
logged instead of emailed and logins would fail.

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
