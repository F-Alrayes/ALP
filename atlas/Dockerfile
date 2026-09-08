# Atlas — a self-contained Streamlit prototype.
# Build:  docker build -t atlas .
# Run:    docker run --rm -p 8501:8501 atlas
#
# Hosts that inject a $PORT (Render, Railway, Cloud Run, Fly) are handled by the
# entrypoint below; it falls back to 8501 when $PORT is unset.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_FILE_WATCHER_TYPE=none

WORKDIR /app

# Dependencies first so the layer caches across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Seed at build time so the first request is instant. The app re-seeds itself if
# the database is missing at runtime, so an ephemeral filesystem is fine too.
RUN python run.py --seed-only

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8501') + '/_stcore/health')" || exit 1

CMD ["sh", "-c", "streamlit run app.py --server.port ${PORT:-8501} --server.address 0.0.0.0 --server.headless true"]
