#!/usr/bin/env bash
# Server for Playwright e2e runs. Runs against the TEST environment
# (.test_env) so the e2e tests' destructive actions (Delete Database,
# delete/import flows) hit the throwaway test database under
# tests/test_files/mount — NEVER the dev database. Previously this used
# the development env, which meant a Playwright run wiped real dev data.
# Forces email "dev mode" with a fixed login code so the email-code
# login flow is deterministic (no real email needed). DEV_LOGIN_CODE
# here MUST match the one in .playwright_env that the tests type in.
export PYTHON_ENVIRONMENT=test
export EMAIL_DEV_MODE=true
export DEV_LOGIN_CODE=123456
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
