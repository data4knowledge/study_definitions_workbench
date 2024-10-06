# Study Definitions Workbench

The swiss army knife for USDM study definitions

# Environment Variables

The following variables are required for authentication and the server. Note that for a single user version the Auth0 variables can be blank:

| Variable | Description |
| :--- | :--- |
| AUTH0_SESSION_SECRET | Session Secret |
| AUTH0_DOMAIN  | Auth0 domain |
| AUTH0_CLIENT_ID | Auth0 client id |
| AUTH0_CLIENT_SECRET | Auth0 client secret |
| AUTH0_AUDIENCE | Auth0 audience key |
| ROOT_URL | Set to the root URL of the server |

The following other environment varaibles are also required:

| Variable | Description |
| :--- | :--- |
| MNT_PATH | The root mount path |
| DATABASE_PATH | The path where the DB will reside |
| DATABASE_NAME | The name of the database file, 'production.db' for example |
| DATAFILE_PATH | The path where the datafiles will reside |
| ADDRESS_SERVER_URL | URL for the address server |
| SINGLE_USER | 'True' for single user environment, 'False' otherwise |

# Fly Deployment

## Creating a volume

```
fly volumes create <name>
fly secrets set DATABASE_URL=sqlite:////mnt/<name>/production.db
fly secrets set DATAFILE_URL=/mnt/<name> 
```

Run on one machine at the moment, sharing of file store is an issue as well as database

```
fly machine destroy e7843d41a59078 --force
fly deploy --ha=false
```

## Separate Applications

With ```fly```command line utility use ```-a <app name>``` to address the production and staging applications
Note the separate ```.toml``` configuration files

# Docker

## Build & Run using Compose

```
docker build . -t data4knowledge/sdw:latest 
docker compose up   
```

Set the environment variables using a ```.env``` file.

## Build and Run using Docker

```
docker build . -t data4knowledge/sdw:latest 
docker volume create sdw_data
docker run -d  --mount source=sdw_data,target=/mount -p 8000:8000 data4knowledge/sdw:latest
```

Set the environment variables using a ```.env``` file.

## Run using Docker Desktop

The image can also be run. obviously, using Docker desktop. Set the environment variables using the launch interface.

## Environment Variables with Docker Image

For all of these the following environment variables need to be set. The remainder are set within the docker file itself

- AUTH0_SESSION_SECRET
- AUTH0_DOMAIN
- AUTH0_CLIENT_ID
- AUTH0_CLIENT_SECRET
- AUTH0_AUDIENCE
- ROOT_URL
- SINGLE_USER
