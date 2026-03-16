#!/bin/bash
set -e
cd "$(dirname "$0")"

# --- Prerequisites ---

if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in your API keys."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed. Install it from https://nodejs.org"
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

mkdir -p data

export PYTHONPATH="$(pwd)"

# --- Install frontend dependencies ---

echo "Installing frontend dependencies..."
(cd frontend && npm install)

# --- Start services ---

uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Waiting for backend to be ready..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "Backend is ready."
        break
    fi
    if [ $i -eq 30 ]; then
        echo "ERROR: Backend failed to start within 30 seconds."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

(cd frontend && npm run dev -- --port 5173) &
FRONTEND_PID=$!

echo ""
echo "Backend running on http://localhost:8000 (PID: $BACKEND_PID)"
echo "Frontend running on http://localhost:5173 (PID: $FRONTEND_PID)"
echo ""
echo "Press Ctrl+C to stop both."

cleanup() {
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM
wait
