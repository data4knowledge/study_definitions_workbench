rm .env
echo ROOT_URL="http://0.0.0.0:8000" >> .env
echo SINGLE_USER=True >> .env
echo FILE_PICKER="pfda" >> .env
docker image pull data4knowledge/sdw:v0.18.1
docker volume create sdw_data
docker run -d --env-file .env --mount source=sdw_data,target=/mount -p 8080:8000 data4knowledge/sdw:v0.18.1 