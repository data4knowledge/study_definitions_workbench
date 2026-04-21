# Deployment Guide — Study Definitions Workbench

This document summarises the deployment options for the Study Definitions Workbench (SDW), a FastAPI web application served by Uvicorn on port 8000.

## Environment Variables

The application has two modes controlled by the `SINGLE_USER` variable:

- **`SINGLE_USER=True`** — Single-user mode. No authentication is required and **all Auth0 variables can be omitted entirely**. This is the simplest configuration for local or personal use.
- **`SINGLE_USER=False`** — Multi-user mode. All Auth0 variables listed below **must** be provided with valid values.

### Authentication (Auth0) — only required when `SINGLE_USER=False`

| Variable | Description |
| :--- | :--- |
| `AUTH0_SESSION_SECRET` | Session secret |
| `AUTH0_DOMAIN` | Auth0 domain |
| `AUTH0_CLIENT_ID` | Auth0 client id |
| `AUTH0_CLIENT_SECRET` | Auth0 client secret |
| `AUTH0_AUDIENCE` | Auth0 audience key |
| `AUTH0_MNGT_CLIENT_ID` | Auth0 management API client id |
| `AUTH0_MNGT_CLIENT_SECRET` | Auth0 management API client secret |

### Application

| Variable | Description |
| :--- | :--- |
| `ROOT_URL` | The server's base URL (deprecated but still accepted) |
| `MNT_PATH` | Root mount path for persistent storage |
| `DATABASE_PATH` | Directory where the SQLite database resides |
| `DATABASE_NAME` | Database filename (e.g. `production.db`) |
| `DATAFILE_PATH` | Directory for uploaded/generated data files |
| `LOCALFILE_PATH` | Path to local files within the volume |
| `CDISC_CORE_CACHE_PATH` | Directory for the CDISC CORE validation cache (JSONata files, XSD schemas, rules, CT packages). Should live on the mounted volume so it survives restarts — a cold cache can take several minutes to rebuild. Leave unset to fall through to the USDM4 platform default (ephemeral inside a container). |
| `ADDRESS_SERVER_URL` | URL for the external address server |
| `SINGLE_USER` | `True` for single-user mode, `False` for multi-user (see above) |
| `FILE_PICKER` | `browser` for standard browser uploads, `os` for the built-in server-side picker |

When running via Docker, the Dockerfile pre-sets `MNT_PATH`, `DATABASE_PATH`, `DATABASE_NAME`, `DATAFILE_PATH`, `LOCALFILE_PATH`, `CDISC_CORE_CACHE_PATH`, and `ADDRESS_SERVER_URL`, so only `SINGLE_USER`, `FILE_PICKER`, and (if multi-user) the Auth0 variables need to be supplied externally.

---

## Persistent Storage (Docker Volume)

The application stores its SQLite database, uploaded data files, and local files on disk. In Docker these paths all live under `/mount` inside the container (as set by the Dockerfile). **A Docker volume must be mounted at `/mount` so that this data survives container restarts and re-deployments.** Without a volume, all data is lost when the container stops.

The volume provides four directories (created automatically by the application on first run):

| Container path | Purpose |
| :--- | :--- |
| `/mount/database` | SQLite database file |
| `/mount/datafiles` | Uploaded and generated data files |
| `/mount/localfiles` | Local working files |
| `/mount/core_cache` | CDISC CORE validation cache (rules, JSONata files, XSD schemas, CT packages) |

You have two ways to provide this volume — Docker Compose (Option 1) creates and manages it for you, or you create one by hand and mount it with `docker run` (Option 2). **These two paths produce independent volumes**; see the note under Option 2 if you're switching between them.

To list existing volumes at any point:

```bash
docker volume ls
```

---

## Option 1 — Docker Compose (recommended for local / self-hosted)

This is the simplest way to run the application locally or on a single server. Docker Compose automatically creates and manages the volume for you.

1. **Create a `.docker_env` file** with the required environment variables. For a minimal single-user setup this is just:
   ```
   SINGLE_USER=True
   FILE_PICKER=browser
   ```
   For multi-user mode, add all the Auth0 variables as well.

2. **Build and start:**
   ```bash
   docker build . -t data4knowledge/sdw:latest
   docker compose up
   ```

   Compose reads `compose.yml`, which declares a named volume `sdw_data` mounted at `/mount` inside the container. On the first `up`, Compose **creates the volume automatically** — you do not need to run `docker volume create` yourself. On every subsequent `up`, Compose **reuses the same volume**, so your database, data files, local files, and CDISC CORE cache all persist across container restarts and image upgrades.

3. **Stop the container:**
   ```bash
   docker compose down       # stops containers, KEEPS the volume (and your data)
   docker compose down -v    # stops containers AND DELETES the volume (data is gone)
   ```

   Use `down` for everyday restarts; only use `down -v` if you deliberately want a clean slate.

**Volume naming note.** Compose prefixes the volume name with the project name, so `docker volume ls` will show something like `study_definitions_workbench_sdw_data`, not bare `sdw_data`. This only matters if you want to inspect, back up, or reuse the volume outside Compose — use the prefixed name in those commands.

---

## Option 2 — Docker Run (manual)

When running without Compose you must **create the volume yourself** before starting the container:

```bash
# 1. Build the image
docker build . -t data4knowledge/sdw:latest -t data4knowledge/sdw:<version>

# 2. Create a named volume (only needed once — persists until explicitly removed)
docker volume create sdw_data

# 3. Run the container, mounting the volume at /mount
docker run -d \
  --mount source=sdw_data,target=/mount \
  -p 8000:8000 \
  --env-file .env \
  data4knowledge/sdw:latest
```

The `--mount source=sdw_data,target=/mount` flag connects the named volume to the container's `/mount` directory. As long as you use the same volume name (`sdw_data`) when restarting or upgrading the container, all database and file data is preserved. The volume is **not** deleted when you `docker stop` or `docker rm` the container — use `docker volume rm sdw_data` for that.

To inspect or back up the volume:
```bash
docker volume inspect sdw_data
```

**This volume is independent of Compose's volume.** The bare `sdw_data` you create here is a different volume from the `<project>_sdw_data` that Compose creates in Option 1 — data does **not** flow between the two. If you start with Compose and later switch to manual `docker run` (or vice versa), your existing data stays with whichever path created it. Pick one path per environment and stick with it.

---

## Option 3 — Docker Desktop

The published image (`data4knowledge/sdw`) can be run directly from Docker Desktop. When configuring the container through the launch interface:

- Map port **8000**
- Set the required environment variables
- Under **Volumes**, create or select a volume and mount it at `/mount` to ensure data persistence

---

## Option 4 — Fly.io (cloud hosting)

The project includes separate Fly.io configuration files for production and staging:

- `fly_production.toml` — app `d4k-sdw`, region `ams`, 4 GB RAM, 2 performance CPUs
- `fly_staging.toml` — app `d4k-sdw-staging`, region `ams`, 1 GB RAM, 1 shared CPU

Both configurations reference a pre-built Docker image from Docker Hub rather than building on Fly.io directly, and mount a persistent Fly volume for the database and data files.

### Deploy steps

```bash
# First-time launch (choose the appropriate .toml file)
fly launch --no-deploy -c fly_production.toml --ha=false

# Set secrets (all on one line, space-separated)
fly secrets set -a d4k-sdw AUTH0_SESSION_SECRET="..." AUTH0_DOMAIN="..." ...

# Set storage paths
fly secrets set -a d4k-sdw MNT_PATH="/mnt/sdw_data" DATABASE_PATH="/mnt/sdw_data/database" DATABASE_NAME="production.db" DATAFILE_PATH="/mnt/sdw_data/datafiles" LOCALFILE_PATH="/mnt/sdw_data/localfiles" CDISC_CORE_CACHE_PATH="/mnt/sdw_data/core_cache"

# Deploy
fly deploy -c fly_production.toml
```

Key notes:
- The `--ha=false` flag restricts deployment to a single machine (required because the SQLite database and file store are not designed for shared access across multiple instances).
- The `-c` flag selects the correct `.toml` configuration for production vs staging.
- After initial deployment, use `-a <app-name>` to address the correct application with the `fly` CLI.
- A Fly volume is created automatically from the `[[mounts]]` section in the `.toml` file.

---

## Multi-Platform Docker Builds

To publish images for both `linux/amd64` and `linux/arm64`:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t data4knowledge/sdw:<tag> . --push
docker manifest inspect data4knowledge/sdw:<tag>
```

Tags should **not** include a `v` prefix (e.g. use `0.35.1`, not `v0.35.1`).

---

## Deployment Checklist

1. Unit tests pass (`python -m pytest --ignore=tests/playwright`)
2. Deploy to staging and verify
3. Playwright end-to-end tests pass
4. Deploy to production and verify
5. Build and push Docker image (tagged with version **and** `latest`)
6. Tag the release in GitHub
7. Check pFDA
8. Write GitHub release notes
9. Update version and release notes for the next release
