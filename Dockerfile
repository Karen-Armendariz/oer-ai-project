FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY data data

ENV PYTHONPATH=/app
ENV HF_HOME=/app/.cache/huggingface

RUN mkdir -p /app/data/chroma_db

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)"

CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
