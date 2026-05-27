#!/usr/bin/env bash
# Server for Playwright e2e runs. Reuses the development env but forces
# email "dev mode" with a fixed login code so the email-code login flow
# is deterministic (no real email needed). DEV_LOGIN_CODE here MUST match
# the one in .playwright_env that the tests type in.
export PYTHON_ENVIRONMENT=development
export EMAIL_DEV_MODE=true
export DEV_LOGIN_CODE=123456
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
