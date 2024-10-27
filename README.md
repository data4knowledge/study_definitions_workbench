# Study Definitions Workbench

The swiss army knife for USDM study definitions

# Environment Variables -

The following variables are required for authentication and the server. Note that for a single user version the Auth0 variables can be blank:

| Variable | Description |
| :--- | :--- |
| AUTH0_SESSION_SECRET | Session Secret |
| AUTH0_DOMAIN  | Auth0 domain |
| AUTH0_CLIENT_ID | Auth0 client id |
| AUTH0_CLIENT_SECRET | Auth0 client secret |
| AUTH0_AUDIENCE | Auth0 audience key |
| ROOT_URL | The server's base url |

The following other environment varaibles are also required:

| Variable | Description |
| :--- | :--- |
| MNT_PATH | The root mount path |
| DATABASE_PATH | The path where the DB will reside |
| DATABASE_NAME | The name of the database file, 'production.db' for example |
| DATAFILE_PATH | The path where the datafiles will reside |
| LOCALFILE_PATH | The path to where local files will reside within the volume |
| ADDRESS_SERVER_URL | URL for the address server |
| SINGLE_USER | 'True' for single user environment, 'False' otherwise |

# Fly Deployment

## Deployment

Deploy to fly.io using the following:

```
fly launch --no-deploy -c <fly_production.toml | fly_staging.toml | ... > --ha=false
fly secrets set -a <d4k-sdw | d4k-sdw-staging | ...>  ..... all the secrets, space separated, on one line ....
fly deploy -c <fly_production.toml | fly_staging.toml | ... >
````

Notes:
- Note the option for production, staging or other applications.
- Run on one machine at the moment, sharing of file store is an issue as well as database. The ```-ha``` flag forces the use of a single machine. 
- The ```-c``` flag forces the use of the correct configuration file.
- Once deployed the -a d4k-sdw appplication name flag works

Volumes:
- A volumne is created as part of the deploy (from this bit in the ```.toml``` file)

```
[[mounts]]
  source = '<name>'
  destination = '/mnt/<name>'
```

Using either 'sdw_data' or 'sdw_data_staging' for the names. This gives environment varaibles:

````
fly secrets set MNT_PATH="/mnt/<name>"
fly secrets set DATABASE_PATH="/mnt/<name>/database"
fly secrets set DATABASE_NAME="production.db"
fly secrets set DATAFILE_PATH="/mnt/<name>/datafiles"
```

## Separate Applications

With ```fly```command line utility use ```-a <app name>``` to address the production and staging applications
Note the separate ```.toml``` configuration files. Be careful when launching, they need to address the ```.toml``` files voa the ```-c``` flag

# Docker

## Login

```
docker login
```

## Build & Run using Compose

```
docker build . -t data4knowledge/sdw:latest 
docker compose up   
```

Set the environment variables using a ```.env``` file.

## Build and Run using Docker

```
docker build . -t data4knowledge/sdw:latest -t data4knowledge/sdw:<version>
docker volume create sdw_data
docker run -d  --mount source=sdw_data,target=/mount -p 8000:8000 data4knowledge/sdw:latest
```

Set the environment variables using a ```.env``` file.

## Run using Docker Desktop

The image can also be run. obviously, using Docker desktop. Set the environment variables using the launch interface.

## Multi Platform Builds

````
docker buildx create --name mybuilder --use
docker buildx build --platform linux/amd64,linux/arm64 -t data4knowledge/sdw:<tag>> . --push
docker manifest inspect data4knowledge/sdw:<tag>  
```

## Environment Variables with Docker Image

The following environment variables need to be set (The remainder are set within the docker file itself):

- AUTH0_SESSION_SECRET
- AUTH0_DOMAIN
- AUTH0_CLIENT_ID
- AUTH0_CLIENT_SECRET
- AUTH0_AUDIENCE
- ROOT_URL
- SINGLE_USER

For a single user environment the AUTH0 variables can be empty.