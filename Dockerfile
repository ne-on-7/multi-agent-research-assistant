# syntax=docker/dockerfile:1

# ---------- Stage 1: build the React/Vite frontend ----------
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

# Install deps first (better layer caching)
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# Build the SPA -> produces /app/frontend/dist
COPY frontend/ ./
RUN npm run build


# ---------- Stage 2: Python runtime serving API + built frontend ----------
FROM python:3.11-slim AS runtime

# Avoid .pyc files and unbuffered logs for clean container output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install CPU-only PyTorch first. App Runner has no GPU, so this avoids pulling
# multi-GB CUDA wheels (cudnn/nccl/cusparselt) that torch grabs by default.
# sentence-transformers then reuses this already-installed CPU build.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python deps (runtime only — eval deps stay out of the image on purpose)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image so the first request isn't slow
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application source
COPY api/ ./api/
COPY agents/ ./agents/
COPY services/ ./services/
COPY config/ ./config/

# Copy the built frontend from stage 1 (api/main.py mounts frontend/dist as static)
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8080

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
