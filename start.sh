#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate

uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

PYTHONPATH="$(pwd)" streamlit run ui/app.py &
FRONTEND_PID=$!

echo "Backend running on http://localhost:8000 (PID: $BACKEND_PID)"
echo "Frontend running on http://localhost:8501 (PID: $FRONTEND_PID)"
echo ""
echo "Press Ctrl+C to stop both."

cleanup() {
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM
wait
