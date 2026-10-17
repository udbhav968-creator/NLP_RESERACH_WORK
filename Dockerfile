# EnHi-LMP Legal Meaning Checker — FastAPI backend + web app in one small image.
# Works as-is on Hugging Face Spaces (Docker SDK, port 7860), Render, Railway, Fly.io or any Docker host.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PORT=7860 LMP_DB=/app/api/data/lmp.sqlite3
RUN useradd -m -u 1000 app
WORKDIR /app

COPY api/requirements.txt api/requirements.txt
RUN pip install -r api/requirements.txt

COPY src/legal_features.py src/legal_features.py
COPY data/enhi_lmp.jsonl data/enhi_lmp.jsonl
COPY web/stats640.json web/stats640.json
COPY api api
# Train the model inside the image so the pickle always matches the installed scikit-learn version.
RUN python api/lmp_service.py && mkdir -p api/data && chown -R app:app /app
USER app

EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"7860\")}/api/health')"
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-7860} --proxy-headers --forwarded-allow-ips='*'"]
