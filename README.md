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

Creating a volume

```
fly volumes create <name>
fly secrets set DATABASE_URL=sqlite:////mnt/<name>/production.db
fly secrets set DATAFILE_URL=/mnt/<name> 
```
