FROM python:3.12

# --- Build-time defaults (non-secret paths only) ---
# These are safe defaults baked into the image. Everything sensitive or
# environment-specific is supplied at runtime (compose env_file, or
# `fly secrets set` on Fly) and is NOT baked in here.
ENV MNT_PATH="/mount"
ENV DATABASE_PATH=/mount/database
ENV DATABASE_NAME=/database.db
ENV DATAFILE_PATH=/mount/datafiles
ENV LOCALFILE_PATH=/mount/localfiles
ENV CDISC_CORE_CACHE_PATH=/mount/core_cache
ENV ADDRESS_SERVER_URL="https://d4k-address.fly.dev"

# --- Required runtime env vars (provide via env_file / fly secrets) ---
#   SESSION_SECRET            cookie signing secret (required)
#   SINGLE_USER               True bypasses login; False = email-code auth
#   FILE_PICKER               browser | os | pfda
# Email-code login (required when SINGLE_USER=False so codes can be sent):
#   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
#   REGISTRATION_NOTIFY_EMAIL optional; notified on each new registration
#   EMAIL_DEV_MODE            true = log codes instead of emailing (dev/test)
#   CODE_LENGTH (6), CODE_EXPIRY_MINUTES (10)   optional overrides
# NOTE: in production SMTP must be configured and EMAIL_DEV_MODE off/unset,
# otherwise login codes are only logged and users cannot sign in.

EXPOSE 8000
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
