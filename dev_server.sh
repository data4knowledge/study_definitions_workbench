export PYTHON_ENVIRONMENT=development
PORT="${1:-8000}"
uvicorn app.main:app --reload --port "$PORT" --host 0.0.0.0

