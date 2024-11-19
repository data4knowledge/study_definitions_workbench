mkdir Sanofi		
mkdir Lilly Diabetes	
mkdir Lilly LZZT	
mkdir Alexion		
mkdir M11
pfda download -folder-id 8539458 -output Sanofi		
pfda download -folder-id 8539459 -output Lilly-Diabetes	
pfda download -folder-id 8539460 -output Lilly-LZZT	
pfda download -folder-id 8539461 -output Alexion		
pfda download -folder-id 8539507 -output M11
rm .env
echo SINGLE_USER=True >> .env
echo FILE_PICKER="os" >> .env
docker image pull data4knowledge/sdw:latest
docker volume create sdw_data
docker run -d --env-file .env --mount source=sdw_data,target=/mount -p 8080:8000 data4knowledge/sdw:latest
mkdir /var/lib/docker/volumes/sdw_data/_data/localfiles
mv Sanofi /var/lib/docker/volumes/sdw_data/_data/localfiles
mv Lilly-Diabetes /var/lib/docker/volumes/sdw_data/_data/localfiles
mv Lilly-LZZT /var/lib/docker/volumes/sdw_data/_data/localfiles
mv Alexion /var/lib/docker/volumes/sdw_data/_data/localfiles		
mv M11 /var/lib/docker/volumes/sdw_data/_data/localfiles
