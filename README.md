# Study Definitions Workbench

The swiss army knife for USDM study definitions

# Environment Variables

In additon to the ones required by the d4kms package 

```
AUTH0_SESSION_SECRET=<session secret key>
AUTH0_DOMAIN=<from the Auth0 configuation>
AUTH0_CLIENT_ID=<from the Auth0 configuation>
AUTH0_CLIENT_SECRET=<from the Auth0 configuation>
AUTH0_AUDIENCE=<from the Auth0 configuation>
ROOT_URL=<base URL for the app>
```

the following variables are required for local development

```DATABASE_URL = "sqlite:///./database.db"```

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

Build & run using compose

```
docker build . -t data4knowledge/sdw:latest 
docker compose up   
```

Build and run using vanilla docker

```
docker build . -t data4knowledge/sdw:latest 
docker volume create sdw_data
docker run -d  --mount source=sdw_data,target=/mount -p 8000:8000 data4knowledge/sdw:latest
```

Or can also use Docker desktop
