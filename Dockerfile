FROM python:3.10
ENV MNT_PATH="/mount"
ENV DATABASE_PATH=/mount/database
ENV DATABASE_NAME=/database.db
ENV DATAFILE_PATH=/mount/datafiles
EXPOSE 8000
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]