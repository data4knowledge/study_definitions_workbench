FROM python:3.12
ENV MNT_PATH="/mount"
ENV DATABASE_PATH=/mount/database
ENV DATABASE_NAME=/database.db
ENV DATAFILE_PATH=/mount/datafiles
ENV LOCALFILE_PATH=/mount/localfiles
ENV ADDRESS_SERVER_URL="https://d4k-address.fly.dev"
EXPOSE 8000
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]