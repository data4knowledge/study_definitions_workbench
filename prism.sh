pfda download -folder-id 8535631
rm .env
echo SINGLE_USER=True >> .env
echo FILE_PICKER="os" >> .env
docker image pull data4knowledge/sdw:v0.22.0
docker volume create sdw_data
docker run -d --env-file .env --mount source=sdw_data,target=/mount -p 8080:8000 data4knowledge/sdw:v0.22.0
mkdir /var/lib/docker/volumes/sdw_data/_data/localfiles
mv *docx /var/lib/docker/volumes/sdw_data/_data/localfiles
